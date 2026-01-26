"""
Auditor Agent - Agente ReAct
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Implementação do agente ReAct para auditoria de contratos com suporte async.
"""

import time
import json
import re
from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from adapters.openai_adapter import OpenAIAdapter
from adapters.chromadb_adapter import ChromaDBAdapter
from domain.contract_schema import ContractMetadata
from domain.tools import create_contract_tools
from common.exceptions import AgentError
from common.types import AnalysisResult, AgentStep
from common.logging import get_logger, log_execution_time
from common.metrics import metrics, AuditorMetrics

logger = get_logger(__name__)


class AuditorAgent:
    """
    Agente ReAct para auditoria de contratos bancários.
    
    Segue o padrão ReAct:
    - Reasoning (Thought): Analisa o que precisa fazer
    - Action: Decide qual tool usar
    - Observation: Observa resultado da action
    - Repete até ter informação suficiente
    
    Implementa:
    - Logging estruturado
    - Métricas de performance
    - Suporte sync e async
    """
    
    def __init__(
        self,
        openai_adapter: OpenAIAdapter,
        chromadb_adapter: ChromaDBAdapter,
        max_iterations: int = 10,
        verbose: bool = True,
        prompt_template: Optional[str] = None
    ) -> None:
        """
        Inicializa o agente auditor.
        
        Args:
            openai_adapter: Adapter da OpenAI (LLM)
            chromadb_adapter: Adapter do ChromaDB (vectorstore)
            max_iterations: Máximo de iterações do loop ReAct
            verbose: Se deve exibir pensamento do agente
            prompt_template: Template customizado (opcional)
        """
        self._openai_adapter: OpenAIAdapter = openai_adapter
        self._chromadb_adapter: ChromaDBAdapter = chromadb_adapter
        self._max_iterations: int = max_iterations
        self._verbose: bool = verbose
        
        # Cria tools
        self._tools: List[Tool] = create_contract_tools(chromadb_adapter)
        
        # Carrega prompt template
        self._prompt_template: str = prompt_template or self._get_default_prompt_template()
        
        # Cria agent executor
        self._agent_executor: AgentExecutor = self._create_agent_executor()
        
        logger.info(
            "AuditorAgent initialized",
            extra_data={
                "max_iterations": max_iterations,
                "num_tools": len(self._tools),
                "verbose": verbose
            }
        )
    
    @property
    def openai_adapter(self) -> OpenAIAdapter:
        """Adapter da OpenAI."""
        return self._openai_adapter
    
    @property
    def chromadb_adapter(self) -> ChromaDBAdapter:
        """Adapter do ChromaDB."""
        return self._chromadb_adapter
    
    @property
    def tools(self) -> List[Tool]:
        """Tools disponíveis para o agente."""
        return self._tools
    
    def _get_default_prompt_template(self) -> str:
        """Retorna prompt template padrão do agente."""
        return """Você é um auditor de contratos especializado do Banco Itaú.
Sua tarefa é analisar contratos bancários e extrair metadados estruturados para avaliação de risco.

Você tem acesso às seguintes ferramentas:

{tools}

Use SEMPRE o seguinte formato:

Thought: [seu raciocínio sobre o que precisa descobrir]
Action: [nome da ferramenta: search_contract ou extract_clause]
Action Input: [entrada para a ferramenta]
Observation: [resultado da ferramenta]
... (repita Thought/Action/Action Input/Observation quantas vezes necessário)
Thought: Agora tenho informação suficiente para responder
Final Answer: [sua resposta estruturada em JSON seguindo o schema ContractMetadata]

IMPORTANTE:
- Sempre busque TODAS as informações necessárias antes de dar a Final Answer
- Use search_contract para encontrar informações sobre: garantias, juros, prazos, valores
- Use extract_clause quando precisar do texto exato de uma cláusula específica
- A Final Answer DEVE ser um JSON válido com os campos:
  * garantia_tipo (string)
  * garantia_objeto (string)
  * taxa_juros (float, apenas o número)
  * prazo_meses (int)
  * valor_principal (float)
  * risco_legal (string: "Baixo", "Médio" ou "Alto")
  * compliance_check (boolean)

Pergunta: {input}

{agent_scratchpad}"""
    
    def _create_agent_executor(self) -> AgentExecutor:
        """Cria o AgentExecutor configurado."""
        logger.debug("Creating AgentExecutor")
        
        # Cria prompt
        prompt = PromptTemplate(
            template=self._prompt_template,
            input_variables=["input", "agent_scratchpad", "tools"]
        )
        
        # Cria agent ReAct
        agent = create_react_agent(
            llm=self._openai_adapter.llm,
            tools=self._tools,
            prompt=prompt
        )
        
        # Cria executor
        executor = AgentExecutor(
            agent=agent,
            tools=self._tools,
            verbose=self._verbose,
            max_iterations=self._max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.debug("AgentExecutor created successfully")
        return executor
    
    def _get_default_query(self) -> str:
        """Retorna query padrão para análise de contrato."""
        return """
        Analyze this banking contract thoroughly and extract:
        
        1. Type and object of guarantee (garantia_tipo, garantia_objeto)
        2. Interest rate per month (taxa_juros)
        3. Contract term in months (prazo_meses)
        4. Principal amount in reais (valor_principal)
        5. Legal risk assessment: "Baixo", "Médio" or "Alto" (risco_legal)
        6. Compliance status: true or false (compliance_check)
        
        Return ONLY a valid JSON following the ContractMetadata schema.
        """
    
    @log_execution_time()
    def analyze_contract(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa contrato e extrai metadados.
        
        Args:
            query: Query customizada (opcional)
            
        Returns:
            Dict com 'output' (JSON) e 'intermediate_steps'
            
        Raises:
            AgentError: Se houver erro na análise
        """
        query = query or self._get_default_query()
        start_time = time.perf_counter()
        
        try:
            logger.info(
                "Starting contract analysis",
                extra_data={"query_length": len(query)}
            )
            
            with AuditorMetrics.track_analysis():
                # Executa agent
                result = self._agent_executor.invoke({"input": query})
            
            duration = time.perf_counter() - start_time
            
            # Registra métricas
            stats = self.get_statistics(result)
            metrics.increment(AuditorMetrics.CONTRACTS_ANALYZED)
            
            logger.info(
                "Contract analysis completed",
                extra_data={
                    "duration_seconds": round(duration, 2),
                    "num_iterations": stats["num_iterations"],
                    "num_tool_calls": stats["num_tool_calls"]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error during contract analysis",
                extra_data={"query_length": len(query), "error": str(e)}
            )
            metrics.increment(AuditorMetrics.CONTRACTS_ERRORS)
            raise AgentError(
                f"Erro ao analisar contrato: {str(e)}",
                details={"query_length": len(query)}
            )
    
    async def aanalyze_contract(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Analisa contrato e extrai metadados (async).
        
        Args:
            query: Query customizada (opcional)
            
        Returns:
            Dict com 'output' (JSON) e 'intermediate_steps'
            
        Raises:
            AgentError: Se houver erro na análise
        """
        query = query or self._get_default_query()
        start_time = time.perf_counter()
        
        try:
            logger.info(
                "Starting contract analysis (async)",
                extra_data={"query_length": len(query)}
            )
            
            with AuditorMetrics.track_analysis():
                # Executa agent async
                result = await self._agent_executor.ainvoke({"input": query})
            
            duration = time.perf_counter() - start_time
            
            # Registra métricas
            stats = self.get_statistics(result)
            metrics.increment(AuditorMetrics.CONTRACTS_ANALYZED)
            
            logger.info(
                "Contract analysis completed (async)",
                extra_data={
                    "duration_seconds": round(duration, 2),
                    "num_iterations": stats["num_iterations"],
                    "num_tool_calls": stats["num_tool_calls"]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error during contract analysis (async)",
                extra_data={"query_length": len(query), "error": str(e)}
            )
            metrics.increment(AuditorMetrics.CONTRACTS_ERRORS)
            raise AgentError(
                f"Erro ao analisar contrato: {str(e)}",
                details={"query_length": len(query)}
            )
    
    def parse_result_to_schema(self, result: Dict[str, Any]) -> ContractMetadata:
        """
        Parseia resultado do agente para ContractMetadata.
        
        Args:
            result: Resultado do agent_executor.invoke()
            
        Returns:
            Instância de ContractMetadata validada
            
        Raises:
            AgentError: Se não conseguir parsear o resultado
        """
        output_text: str = ""
        data: Optional[Dict[str, Any]] = None
        
        try:
            output_text = result["output"]
            
            logger.debug(
                "Parsing agent result to schema",
                extra_data={"output_length": len(output_text)}
            )
            
            # Procura por JSON no texto
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            
            if not json_match:
                logger.error(
                    "No JSON found in agent output",
                    extra_data={"output_preview": output_text[:200]}
                )
                raise AgentError(
                    "Não foi possível encontrar JSON no output do agente",
                    details={"output": output_text[:200]}
                )
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # Valida com Pydantic
            metadata = ContractMetadata(**data)
            
            logger.info(
                "Result parsed successfully",
                extra_data={"risk_level": metadata.risco_legal}
            )
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(
                "JSON decode error",
                extra_data={"error": str(e), "output_preview": output_text[:200]}
            )
            raise AgentError(
                f"Erro ao parsear JSON: {str(e)}",
                details={"output": output_text[:200]}
            )
        except AgentError:
            raise
        except Exception as e:
            logger.error(
                "Error creating ContractMetadata",
                extra_data={"error": str(e), "data": str(data) if data else None}
            )
            raise AgentError(
                f"Erro ao criar ContractMetadata: {str(e)}",
                details={"data": str(data) if data else None}
            )
    
    def analyze_and_parse(self, query: Optional[str] = None) -> ContractMetadata:
        """
        Analisa contrato e retorna ContractMetadata validado.
        
        Combina analyze_contract() + parse_result_to_schema().
        
        Args:
            query: Query customizada (opcional)
            
        Returns:
            ContractMetadata validado
        """
        result = self.analyze_contract(query)
        return self.parse_result_to_schema(result)
    
    async def aanalyze_and_parse(self, query: Optional[str] = None) -> ContractMetadata:
        """
        Analisa contrato e retorna ContractMetadata validado (async).
        
        Combina aanalyze_contract() + parse_result_to_schema().
        
        Args:
            query: Query customizada (opcional)
            
        Returns:
            ContractMetadata validado
        """
        result = await self.aanalyze_contract(query)
        return self.parse_result_to_schema(result)
    
    def get_statistics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai estatísticas da execução do agente.
        
        Args:
            result: Resultado do agent_executor.invoke()
            
        Returns:
            Dict com estatísticas
        """
        intermediate_steps = result.get("intermediate_steps", [])
        
        tools_used: List[str] = []
        for step in intermediate_steps:
            if len(step) >= 1:
                action = step[0]
                tools_used.append(action.tool)
                # Registra métrica de tool call
                metrics.increment(
                    AuditorMetrics.TOOL_CALLS,
                    labels={"tool": action.tool}
                )
        
        return {
            "num_iterations": len(intermediate_steps),
            "tools_used": tools_used,
            "unique_tools": list(set(tools_used)),
            "num_tool_calls": len(tools_used)
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo das métricas do auditor.
        
        Returns:
            Dict com métricas agregadas
        """
        return metrics.get_all_metrics()
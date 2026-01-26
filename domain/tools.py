"""
Tools Definition - Ferramentas do Agente
Auditor de Contratos - Bootcamp Itaú FIAP 2026

Define as tools que o agente pode usar para interagir com contratos.
"""

from typing import List, TYPE_CHECKING
from langchain.tools import Tool

if TYPE_CHECKING:
    from adapters.chromadb_adapter import ChromaDBAdapter


def create_contract_tools(vectorstore_adapter: "ChromaDBAdapter") -> List[Tool]:
    """
    Cria lista de tools para o agente usar.
    
    Args:
        vectorstore_adapter: Adapter do ChromaDB para buscar informações
        
    Returns:
        Lista de objetos Tool do LangChain
    """
    
    def search_contract(query: str) -> str:
        """
        Busca chunks relevantes no contrato usando similaridade semântica.
        
        Args:
            query: Pergunta ou palavra-chave sobre o contrato (português ou inglês)
            
        Returns:
            String com chunks encontrados formatados
            
        Examples:
            >>> search_contract("garantias")
            >>> search_contract("interest rate")
            >>> search_contract("prazo do contrato")
        """
        try:
            docs = vectorstore_adapter.search(query, k=3)
            
            if not docs:
                return "Nenhum chunk relevante encontrado para esta query."
            
            # Formata resultado com separadores
            chunks_text = []
            for i, doc in enumerate(docs, 1):
                chunks_text.append(f"Chunk {i}:\n{doc.page_content}")
            
            context = "\n\n---\n\n".join(chunks_text)
            return f"Chunks encontrados:\n\n{context}"
            
        except Exception as e:
            return f"Erro ao buscar no contrato: {str(e)}"
    
    def extract_clause(clause_number: str) -> str:
        """
        Extrai cláusula específica do contrato por número.
        
        Args:
            clause_number: Número da cláusula (ex: '4', '5.1', 'QUARTA')
            
        Returns:
            Texto da cláusula ou mensagem de erro
            
        Examples:
            >>> extract_clause("4")
            >>> extract_clause("5.1")
            >>> extract_clause("QUARTA")
        """
        try:
            # Normaliza o número da cláusula
            clause_upper = clause_number.upper()
            
            # Formata query para buscar cláusula
            query = f"CLÁUSULA {clause_upper}"
            docs = vectorstore_adapter.search(query, k=1)
            
            if docs:
                return f"Cláusula {clause_number}:\n\n{docs[0].page_content}"
            else:
                return f"❌ Cláusula {clause_number} não encontrada no contrato."
                
        except Exception as e:
            return f"Erro ao extrair cláusula: {str(e)}"
    
    # Retorna lista de Tools configuradas
    return [
        Tool(
            name="search_contract",
            func=search_contract,
            description=(
                "Use this tool to search for information in the contract. "
                "Input should be a question or keyword (in Portuguese or English). "
                "Examples: 'garantias', 'interest rate', 'prazo', 'penalties'. "
                "Returns the top 3 most relevant chunks from the contract."
            )
        ),
        Tool(
            name="extract_clause",
            func=extract_clause,
            description=(
                "Use this tool to extract a specific clause by number from the contract. "
                "Input should be the clause number like '4', '5.1', or 'QUARTA'. "
                "Returns the full text of that specific clause."
            )
        )
    ]


def create_financial_calculator_tool() -> Tool:
    """
    Tool adicional para cálculos financeiros.
    Exemplo de como estender o sistema com novas tools.
    """
    
    def calculate_compound_interest(params: str) -> str:
        """
        Calcula juros compostos.
        
        Args:
            params: String no formato "principal,rate,months"
                   ex: "1500000,1.0,36"
        """
        try:
            principal, rate, months = params.split(",")
            principal = float(principal)
            rate = float(rate) / 100  # Converter para decimal
            months = int(months)
            
            montante = principal * ((1 + rate) ** months)
            juros = montante - principal
            
            return f"""
Cálculo de Juros Compostos:
• Principal: R$ {principal:,.2f}
• Taxa: {rate * 100}% ao mês
• Prazo: {months} meses
• Montante Final: R$ {montante:,.2f}
• Juros Totais: R$ {juros:,.2f}
            """.strip()
            
        except Exception as e:
            return f"Erro no cálculo: {str(e)}. Use formato: principal,rate,months"
    
    return Tool(
        name="calculate_interest",
        func=calculate_compound_interest,
        description=(
            "Calculate compound interest for a loan. "
            "Input format: 'principal,rate,months' "
            "Example: '1500000,1.0,36' for R$ 1.5M at 1% monthly for 36 months"
        )
    )

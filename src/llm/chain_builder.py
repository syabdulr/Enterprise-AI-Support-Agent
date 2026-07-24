"""
LangChain chain builders for different agent workflows.
Creates specialized chains for triage, diagnosis, resolution, and escalation.
"""

from typing import Dict, Optional, List
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from .azure_openai_client import AzureOpenAIClient
from .prompts import (
    TRIAGE_SYSTEM_PROMPT,
    DIAGNOSIS_SYSTEM_PROMPT,
    RESOLUTION_SYSTEM_PROMPT,
    ESCALATION_SYSTEM_PROMPT,
    HUMAN_REVIEW_PROMPT
)


class ChainBuilder:
    """Build specialized LangChain chains for different agent workflows."""
    
    def __init__(self, client: AzureOpenAIClient):
        """Initialize chain builder with Azure OpenAI client."""
        self.client = client
    
    def build_triage_chain(self) -> LLMChain:
        """Build chain for incident triage and categorization."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", TRIAGE_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.client.chat_model | StrOutputParser()
        return chain
    
    def build_diagnosis_chain(self) -> LLMChain:
        """Build chain for incident diagnosis and root cause analysis."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", DIAGNOSIS_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.client.chat_model | StrOutputParser()
        return chain
    
    def build_resolution_chain(self) -> LLMChain:
        """Build chain for incident resolution and solution generation."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", RESOLUTION_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.client.chat_model | StrOutputParser()
        return chain
    
    def build_escalation_chain(self) -> LLMChain:
        """Build chain for incident escalation and human handoff."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", ESCALATION_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.client.chat_model | StrOutputParser()
        return chain
    
    def build_rag_chain(self, retriever):
        """Build conversational retrieval chain with RAG."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant for incident resolution. "
                       "Use the following retrieved context to answer questions. "
                       "If you don't know the answer from the context, say so.\n\n"
                       "Context: {context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.client.chat_model,
            retriever=retriever,
            memory=memory,
            prompt=prompt
        )
        
        return chain
    
    def build_structured_output_chain(
        self,
        system_prompt: str,
        output_schema: Dict[str, Any]
    ) -> LLMChain:
        """Build chain that outputs structured JSON."""
        parser = JsonOutputParser()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"{system_prompt}\n\n{parser.get_format_instructions()}"),
            ("human", "{input}")
        ])
        
        chain = prompt | self.client.chat_model | parser
        return chain
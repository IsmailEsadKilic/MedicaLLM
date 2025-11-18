from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document

import printmeup as pm
from typing import List, Literal

class RAGChain:
    
    def __init__(self, 
                 retriever: VectorStoreRetriever,
                 ollama_model_name: str,
                 ollama_base_url: str,
                 temperature: float = 0.7):
        """
        Args:
            retriever: Retriever from Vector Store
            ollama_model_name: Ollama model name
            ollama_base_url: Ollama base URL
            temperature: Model temperature between 0 and 1
        """
        self.retriever = retriever
        self.ollama_model_name = ollama_model_name
        self.temperature = temperature
        self.chat_history = list[tuple[str, str]]() # * (human, ai)
        
        self.llm = ChatOllama(
            model=self.ollama_model_name,
            temperature=temperature,
            base_url=ollama_base_url
        )
        
        self.qa_prompt: ChatPromptTemplate
        self.conversational_prompt: ChatPromptTemplate
        
        self.qa_chain: Runnable
        self.conversational_chain: Runnable
        
        self._create_chains()
    
    def _create_chains(self):        
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a helpful AI assistant. Answer the question using the context information below.

Context:
{context}

Important rules:
- Only use the given context information
- If you cannot find the answer in the context, say you don't know
- Provide detailed and explanatory answers
- You can answer in Turkish or English
"""         ),
            ("human", "{question}")
        ])
        
        self.conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a helpful AI assistant. Answer the question using the previous conversation history and the context information below.

Conversation History:
{chat_history}

Context:
{context}

Important rules:
- Remember previous conversations and be consistent
- Only use the given context information
- Provide detailed and explanatory answers
"""         ),
            ("human", "{question}")
        ])
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.qa_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.qa_prompt
            | self.llm
            | StrOutputParser()
        )
        
        self.conversational_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.conversational_prompt
            | self.llm
            | StrOutputParser()
        )
        
        pm.suc("Rag chains created")
    
    def query(self, question: str, chain_type: Literal["qa", "conversational"] = "qa") -> dict:
        """
        Returns:
            dict: {"answer": str, "source_documents": List[Document]}
        """
        print(f"\n💬 Soru: {question}")
        print(f"🔗 Chain tipi: {chain_type}\n")
        
        try:
            source_docs = self.retriever.invoke(question)
            
            if chain_type == "qa":
                answer = self.qa_chain.invoke(question)
                
            elif chain_type == "conversational":
                history_text = "\n".join([f"Human: {h[0]}\nAI: {h[1]}" for h in self.chat_history[-3:]])
                context = "\n\n".join([doc.page_content for doc in source_docs])
                
                messages = self.conversational_prompt.format_messages(
                    chat_history=history_text,
                    context=context,
                    question=question
                )
                
                response = self.llm.invoke(messages)
                answer = response.content
                
                # HACK
                if isinstance(answer, (list, str)):
                    answer = "".join(answer) # type: ignore
                elif isinstance(answer, (list, dict)):
                    answer = "".join([str(a) for a in answer]) # type: ignore
                answer = str(answer)
                
                self.chat_history.append((question, answer))
            
            response = {
                "answer": answer,
                "source_documents": source_docs
            }
            
            if chain_type == "conversational":
                response["chat_history"] = self.chat_history
                
            return response
        except Exception as e:
            pm.err(e)
            return {
                "answer": e.__repr__(),
                "source_documents": []
            }
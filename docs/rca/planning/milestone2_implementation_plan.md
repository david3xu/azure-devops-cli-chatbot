# Milestone 2: GraphRAG Implementation Plan

**Last Updated**: March 17, 2024  
**Current Milestone**: Transitioning from Milestone 1 to Milestone 2  
**Focus**: Knowledge Graph Integration and Enhanced Query Processing

## 1. Current Status

Milestone 1 has been successfully implemented with the following components:

- ✅ **Agent Architecture**: Pydantic-based agent with workflow tracking
- ✅ **Tool System**: Vector search, document ranking, and response generation tools
- ✅ **Azure Integration**: OpenAI and Azure Search connectors
- ✅ **API Layer**: FastAPI endpoints with HTML visualization
- ✅ **Testing**: Comprehensive test suite for all components
- ✅ **Documentation**: README and architecture diagrams
- ✅ **Workflow Visualization**: HTML-based visualization for agent workflow

The system currently follows a straightforward RAG pipeline:
```
User Query → Vector Search → Document Ranking → Response Generation
```

## 2. Milestone 2 Objectives

GraphRAG extends the basic RAG approach with:

1. **Query Optimization**: Using LLM to reformulate and enhance queries
2. **Knowledge Graph Integration**: Capturing entity relationships
3. **Community Detection**: Identifying topic clusters for contextual retrieval
4. **Strategy Factory**: Multiple search approaches tailored to query types

The enhanced pipeline will be:
```
User Query → Query Understanding → Strategy Selection → Enhanced Retrieval → Response Generation
```

## 3. Implementation Plan

### Phase 1: Query Optimization (Week 1)

1. **Query Analyzer Tool** (Priority: High)
   - Create `src/rca/tools/query_tools.py` for query analysis and reformulation
   - Implement Pydantic models for query understanding outputs
   - Develop prompt templates for query enhancement
   - Add tests for query optimization

2. **Prompt Management System** (Priority: Medium)
   - Create `src/rca/prompts/` directory with template management
   - Implement variable substitution and context management
   - Add caching for prompt templates

3. **Enhanced Orchestration** (Priority: High)
   - Update `RCAAgent` to include query optimization step
   - Track additional steps in workflow visualization
   - Modify workflow to support pre-retrieval processing

### Phase 2: Knowledge Graph Integration (Week 2)

1. **Entity Extraction** (Priority: High)
   - Create `src/rca/tools/entity_tools.py` for entity recognition
   - Implement Pydantic models for entity data
   - Integrate with Azure Text Analytics or LLM for extraction

2. **Graph Connector** (Priority: High)
   - Create `src/rca/connectors/graph_connector.py` for Cosmos DB integration
   - Implement entity and relationship storage
   - Add query capabilities for graph traversal

3. **Graph Schema Design** (Priority: Medium)
   - Define entity types and relationship models
   - Create schema validation utilities
   - Implement graph population workflow

### Phase 3: Search Strategy Implementation (Week 3)

1. **Strategy Factory** (Priority: High)
   - Create `src/rca/strategies/` directory for search strategies
   - Implement strategy selection based on query type
   - Add Pydantic models for strategy configuration

2. **Global Search Strategy** (Priority: Medium)
   - Implement community summary retrieval
   - Create holistic understanding workflow
   - Add tests comparing with basic search

3. **Local Search Strategy** (Priority: Medium)
   - Implement entity-focused retrieval
   - Optimize for speed with targeted queries
   - Add benchmarks for performance comparison

4. **DRIFT Search Strategy** (Priority: High)
   - Implement entity focus with community expansion
   - Create hybrid retrieval workflow
   - Add evaluation metrics for search quality

### Phase 4: Community Detection (Week 4)

1. **Community Analysis** (Priority: Medium)
   - Create `src/rca/community/` directory for community algorithms
   - Implement graph-based community detection
   - Add hierarchical community structure building

2. **Community Summaries** (Priority: Low)
   - Implement map-reduce summarization of communities
   - Create caching for community summaries
   - Add metrics for summary quality

3. **Integration Testing** (Priority: High)
   - Create end-to-end tests for GraphRAG pipeline
   - Implement comparison metrics against Milestone 1
   - Add documentation for architectural changes

## 4. Azure Integration Details

### New Azure Resources Required

1. **Azure Cosmos DB**
   - Required for: Knowledge graph storage
   - Setup: Create Cosmos DB account with Graph API
   - Cost estimate: ~$50-100/month depending on usage

2. **Azure Functions** (Optional)
   - Required for: Asynchronous entity extraction
   - Setup: Create Functions app for entity processing
   - Cost estimate: Pay-per-execution, ~$20-30/month

### Enhanced Existing Resources

1. **Azure OpenAI Service**
   - New usage: Query optimization, entity extraction
   - Estimated additional tokens: ~20-30% increase
   - Cost impact: Proportional to token increase

2. **Azure AI Search**
   - Enhancements: Integration with knowledge graph results
   - Performance impact: Additional filtering complexity
   - Cost impact: Minimal, within existing tier

## 5. Implementation Tasks Breakdown

### Week 1: Query Optimization

| Day | Task | Est. Hours | Assignee | Status |
|-----|------|------------|----------|--------|
| 1 | Setup development environment | 2 | TBD | Not Started |
| 1 | Create query analysis prompts | 4 | TBD | Not Started |
| 2 | Implement query analyzer tool | 6 | TBD | Not Started |
| 3 | Create prompt management system | 6 | TBD | Not Started |
| 4 | Update agent orchestration | 4 | TBD | Not Started |
| 5 | Write tests for query optimization | 4 | TBD | Not Started |
| 5 | Document query optimization | 2 | TBD | Not Started |

### Week 2: Knowledge Graph Integration

| Day | Task | Est. Hours | Assignee | Status |
|-----|------|------------|----------|--------|
| 1 | Define graph schema | 4 | TBD | Not Started |
| 1-2 | Setup Cosmos DB with Graph API | 6 | TBD | Not Started |
| 2-3 | Implement entity extraction | 8 | TBD | Not Started |
| 3-4 | Create graph connector | 8 | TBD | Not Started |
| 5 | Write tests for graph operations | 4 | TBD | Not Started |
| 5 | Document graph integration | 2 | TBD | Not Started |

### Week 3: Search Strategies

| Day | Task | Est. Hours | Assignee | Status |
|-----|------|------------|----------|--------|
| 1 | Create strategy factory | 4 | TBD | Not Started |
| 1-2 | Implement Global Search | 6 | TBD | Not Started |
| 2-3 | Implement Local Search | 6 | TBD | Not Started |
| 3-4 | Implement DRIFT Search | 8 | TBD | Not Started |
| 5 | Write strategy comparison tests | 4 | TBD | Not Started |
| 5 | Document search strategies | 2 | TBD | Not Started |

### Week 4: Community Detection & Integration

| Day | Task | Est. Hours | Assignee | Status |
|-----|------|------------|----------|--------|
| 1-2 | Implement community detection | 8 | TBD | Not Started |
| 2-3 | Create community summaries | 6 | TBD | Not Started |
| 3-4 | Integrate all components | 8 | TBD | Not Started |
| 4-5 | End-to-end testing | 6 | TBD | Not Started |
| 5 | Final documentation | 4 | TBD | Not Started |

## 6. Technical Specifications

### Query Analyzer Tool

```python
# src/rca/tools/query_tools.py
from pydantic import BaseModel, Field
from typing import List, Optional
from src.rca.tools.base_tool import BaseTool

class QueryAnalysisInput(BaseModel):
    """Input for query analysis"""
    query: str
    conversation_history: Optional[List[dict]] = None

class QueryAnalysisOutput(BaseModel):
    """Output from query analysis"""
    enhanced_query: str
    detected_entities: List[str] = Field(default_factory=list)
    query_type: str = "informational"  # informational, entity-specific, comparative
    suggested_strategy: str = "hybrid"  # global, local, drift

class QueryAnalyzerTool(BaseTool[QueryAnalysisInput, QueryAnalysisOutput]):
    """Tool for analyzing and enhancing user queries"""
    input_model = QueryAnalysisInput
    output_model = QueryAnalysisOutput
    
    def _execute(self, input_data: QueryAnalysisInput) -> dict:
        # Implementation using LLM for query understanding
        # ...
```

### Knowledge Graph Connector

```python
# src/rca/connectors/graph_connector.py
from azure.cosmos.aio import CosmosClient
from typing import List, Dict, Any

class GraphConnector:
    """Connector for Azure Cosmos DB with Graph API"""
    
    def __init__(self):
        # Initialize connection to Cosmos DB
        
    async def add_entity(self, entity_id: str, entity_type: str, properties: Dict[str, Any]) -> str:
        """Add an entity to the graph"""
        # Implementation
        
    async def add_relationship(self, source_id: str, target_id: str, relationship_type: str, properties: Dict[str, Any] = None) -> str:
        """Add a relationship between entities"""
        # Implementation
        
    async def query_related_entities(self, entity_id: str, relationship_types: List[str] = None, max_depth: int = 1) -> List[Dict[str, Any]]:
        """Query entities related to the given entity"""
        # Implementation using Gremlin queries
```

### Strategy Factory

```python
# src/rca/strategies/factory.py
from typing import Dict, Any, Type
from src.rca.strategies.base_strategy import SearchStrategy
from src.rca.strategies.global_strategy import GlobalSearchStrategy
from src.rca.strategies.local_strategy import LocalSearchStrategy
from src.rca.strategies.drift_strategy import DriftSearchStrategy

class StrategyFactory:
    """Factory for creating search strategies based on query analysis"""
    
    def __init__(self):
        self.strategies: Dict[str, Type[SearchStrategy]] = {
            "global": GlobalSearchStrategy,
            "local": LocalSearchStrategy,
            "drift": DriftSearchStrategy
        }
        
    def create_strategy(self, strategy_type: str, **kwargs) -> SearchStrategy:
        """Create a strategy instance based on type"""
        if strategy_type not in self.strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
            
        return self.strategies[strategy_type](**kwargs)
        
    def select_strategy(self, query_analysis: Dict[str, Any]) -> SearchStrategy:
        """Select the appropriate strategy based on query analysis"""
        # Implementation logic to select strategy
        # ...
```

## 7. Progress Tracking

| Component | Status | Completion % | Notes |
|-----------|--------|--------------|-------|
| Query Optimization | Not Started | 0% | - |
| Prompt Management | Not Started | 0% | - |
| Knowledge Graph | Not Started | 0% | - |
| Entity Extraction | Not Started | 0% | - |
| Strategy Factory | Not Started | 0% | - |
| Search Strategies | Not Started | 0% | - |
| Community Detection | Not Started | 0% | - |
| Azure Integration | Not Started | 0% | - |
| Testing & Evaluation | Not Started | 0% | - |
| Documentation | In Progress | 10% | Planning document created |

## 8. Next Steps

1. **Immediate Next Steps**:
   - [ ] Assign developers to Week 1 tasks
   - [ ] Setup Azure Cosmos DB for development
   - [ ] Start implementing query optimization

2. **Key Decisions Needed**:
   - [ ] Finalize graph schema design
   - [ ] Determine metrics for strategy comparison
   - [ ] Choose community detection algorithm

3. **Dependencies**:
   - Query optimization requires existing Azure OpenAI connector
   - Knowledge graph integration requires Cosmos DB setup
   - Strategy selection depends on query optimization and graph connector

## 9. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Cosmos DB performance issues | High | Medium | Design efficient queries, implement caching |
| Query optimization degrades results | High | Low | A/B testing, fallback to basic search |
| Complex implementation delays | Medium | Medium | Prioritize features, use incremental approach |
| API limits for Azure services | Medium | Medium | Implement request batching and rate limiting |
| Integration complexity | Medium | High | Clear interfaces, incremental testing |

This plan will be updated regularly as implementation progresses. 
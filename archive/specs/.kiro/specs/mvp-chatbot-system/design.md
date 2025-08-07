# MVP Chatbot System Design

## Overview

This design addresses the core systematic issues identified in testing while maintaining MVP simplicity. Instead of manual fixes for specific cases, we implement general solutions that scale to handle various product queries and conversation patterns effectively.

## Architecture

### Current Issues Analysis
Based on comprehensive testing (90.6% success rate), the main systematic issues are:

1. **Search Accuracy Issues (7.1% failure rate)**: Products with specific descriptive features not matched correctly
2. **Context Management Failure (66.7% failure rate)**: Follow-up questions not resolved using conversation history
3. **Manual Exception Handling**: Adding specific rules for individual products doesn't scale

### MVP Solution Architecture
```
User Query: "göğüs ve sırt dekolteli takım"
    ↓
┌─────────────────────────────────────────────────────────┐
│              Enhanced Query Processing                  │
│  • Feature Extraction    • Query Expansion             │
│  • Synonym Mapping      • Context Integration          │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│              Intelligent Product Matching              │
│  • Semantic Similarity  • Feature Matching            │
│  • Fuzzy String Match   • Category Filtering           │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│              Simple Context Management                  │
│  • Session Storage      • Product Memory               │
│  • Follow-up Resolution • Context Timeout              │
└─────────────────────────────────────────────────────────┘
    ↓
Correct Result: "Göğüs ve Sırt Dekolteli Brode Dantelli Şort Takımı"
```

## Components and Interfaces

### 1. Enhanced Query Processor

**Component:** `QueryProcessor`
- **Feature Extraction:** Automatically extract product features from queries
- **Query Expansion:** Add synonyms and related terms
- **Context Integration:** Merge current query with conversation context
- **Normalization:** Handle Turkish language variations and typos

**Interface:**
```python
class QueryProcessor:
    def extract_features(self, query: str) -> List[ProductFeature]
    def expand_query(self, query: str) -> str
    def normalize_turkish(self, text: str) -> str
    def integrate_context(self, query: str, context: ConversationContext) -> str
```

**Implementation Strategy:**
```python
# Instead of manual rules, use pattern-based feature extraction
feature_patterns = {
    'dekolte_types': ['göğüs dekolteli', 'sırt dekolteli', 'v yaka', 'açık yaka'],
    'product_types': ['takım', 'set', 'pijama', 'gecelik', 'sabahlık'],
    'materials': ['dantelli', 'brode', 'saten', 'pamuk'],
    'styles': ['etnik', 'afrika', 'desenli', 'düz']
}
```

### 2. Intelligent Product Matcher

**Component:** `ProductMatcher`
- **Multi-Strategy Matching:** Combine semantic, fuzzy, and feature-based matching
- **Confidence Scoring:** Calculate match confidence for result validation
- **Feature Weighting:** Weight different product features based on query context
- **Result Ranking:** Rank results by relevance and confidence

**Interface:**
```python
class ProductMatcher:
    def match_products(self, processed_query: ProcessedQuery, 
                      products: List[Product]) -> List[MatchResult]
    def calculate_confidence(self, query: str, product: Product) -> float
    def rank_results(self, matches: List[MatchResult]) -> List[RankedResult]
```

**Scoring Algorithm:**
```python
def calculate_match_score(query_features, product_features):
    semantic_score = semantic_similarity(query, product_text) * 0.4
    feature_score = feature_overlap(query_features, product_features) * 0.4
    fuzzy_score = fuzzy_match(query, product_name) * 0.2
    
    # Dynamic weighting based on query type
    if query_has_specific_features(query):
        feature_score *= 1.5  # Boost feature matching for specific queries
    
    return min(1.0, semantic_score + feature_score + fuzzy_score)
```

### 3. Simple Context Manager

**Component:** `ContextManager`
- **Session Storage:** Store conversation context per session
- **Product Memory:** Remember discussed products for follow-up questions
- **Context Resolution:** Resolve ambiguous queries using stored context
- **Timeout Management:** Clean up expired contexts

**Interface:**
```python
class ContextManager:
    def store_product_context(self, session_id: str, product: Product)
    def get_context(self, session_id: str) -> Optional[ConversationContext]
    def resolve_followup(self, query: str, context: ConversationContext) -> Optional[str]
    def cleanup_expired(self)
```

**Context Storage:**
```python
@dataclass
class ConversationContext:
    session_id: str
    last_product: Optional[Product]
    last_query_type: str
    timestamp: float
    
    def is_expired(self, timeout: int = 300) -> bool:
        return time.time() - self.timestamp > timeout
```

### 4. Feature-Based Product Indexing

**Component:** `ProductIndexer`
- **Automatic Feature Extraction:** Extract features from product names and descriptions
- **Feature Categorization:** Categorize features by type (color, style, material, etc.)
- **Search Index Creation:** Create searchable indexes for different feature types
- **Dynamic Updates:** Update indexes when products change

**Interface:**
```python
class ProductIndexer:
    def extract_product_features(self, product: Product) -> List[ProductFeature]
    def create_search_index(self, products: List[Product]) -> SearchIndex
    def update_index(self, product: Product)
```

**Feature Extraction:**
```python
def extract_features_from_name(product_name: str) -> List[ProductFeature]:
    features = []
    
    # Pattern-based extraction
    for category, patterns in FEATURE_PATTERNS.items():
        for pattern in patterns:
            if pattern in product_name.lower():
                features.append(ProductFeature(
                    name=pattern,
                    category=category,
                    weight=calculate_feature_weight(pattern, category)
                ))
    
    return features
```

## Data Models

### Enhanced Product Model
```python
@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    features: List[ProductFeature]
    search_text: str  # Enhanced text for searching
    
@dataclass
class ProductFeature:
    name: str
    category: str  # 'dekolte', 'material', 'style', 'type'
    weight: float
    synonyms: List[str]
```

### Query Processing Models
```python
@dataclass
class ProcessedQuery:
    original: str
    normalized: str
    features: List[ProductFeature]
    expanded_terms: List[str]
    query_type: str  # 'search', 'price', 'stock', etc.

@dataclass
class MatchResult:
    product: Product
    confidence: float
    feature_matches: List[FeatureMatch]
    match_explanation: str
```

## Error Handling

### Systematic Error Prevention
1. **Low Confidence Handling:** When match confidence < 0.7, present multiple options
2. **Feature Mismatch Detection:** Detect when query features don't match any products
3. **Context Recovery:** Attempt to recover context from recent conversation history
4. **Graceful Degradation:** Fall back to simpler matching when advanced methods fail

### Error Recovery Strategies
```python
def handle_low_confidence_match(results: List[MatchResult]) -> Response:
    if not results or max(r.confidence for r in results) < 0.7:
        return suggest_alternatives_or_clarification(results)
    
    if len([r for r in results if r.confidence > 0.8]) > 1:
        return present_multiple_options(results)
    
    return return_best_match(results[0])
```

## Testing Strategy

### Systematic Testing Approach
Instead of testing individual product cases, test the system's ability to:

1. **Feature Extraction Accuracy:** Test automatic feature detection across product categories
2. **Query Processing Robustness:** Test with various Turkish language patterns and typos
3. **Context Management Reliability:** Test follow-up question resolution across different scenarios
4. **Confidence Scoring Accuracy:** Validate that confidence scores correlate with actual match quality

### Test Categories
```python
test_categories = {
    'feature_extraction': [
        'dekolte variations', 'material types', 'product categories', 'style descriptors'
    ],
    'query_processing': [
        'turkish_normalization', 'typo_handling', 'synonym_expansion', 'context_integration'
    ],
    'matching_accuracy': [
        'semantic_similarity', 'feature_matching', 'fuzzy_matching', 'result_ranking'
    ],
    'context_management': [
        'context_storage', 'followup_resolution', 'context_timeout', 'context_recovery'
    ]
}
```

## Implementation Phases

### Phase 1: Enhanced Query Processing (Week 1)
- Implement systematic feature extraction from product names
- Create Turkish language normalization with comprehensive rules
- Build query expansion with synonym mapping
- Add context integration for follow-up queries

### Phase 2: Intelligent Product Matching (Week 1-2)
- Implement multi-strategy matching algorithm
- Create confidence scoring system
- Build result ranking and validation
- Add feature-based matching weights

### Phase 3: Simple Context Management (Week 2)
- Implement session-based context storage
- Add follow-up query resolution
- Create context timeout and cleanup
- Build context recovery mechanisms

### Phase 4: Integration and Testing (Week 2-3)
- Integrate all components into existing system
- Run comprehensive testing suite
- Fix systematic issues identified in testing
- Optimize performance and reliability

## Success Metrics

### MVP Success Criteria
- **Overall Success Rate:** >95% (currently 90.6%)
- **Product Search Accuracy:** >95% (currently 92.9%)
- **Context Management:** >80% (currently 33.3%)
- **Response Time:** <2 seconds average
- **Error Recovery:** >90% of errors handled gracefully

### Systematic Improvements
- **Scalability:** System handles new products without manual rules
- **Maintainability:** Feature extraction works across product categories
- **Robustness:** Context management works for various conversation patterns
- **Extensibility:** New businesses can be added through configuration only

This design focuses on systematic solutions that address root causes rather than symptoms, ensuring the MVP can scale and handle diverse scenarios without manual intervention for each case.
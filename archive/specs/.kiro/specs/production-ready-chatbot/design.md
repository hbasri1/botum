# Production-Ready Chatbot Design

## Overview

This design transforms the existing functional chatbot system into a production-ready application by adding essential infrastructure components: cost tracking, performance monitoring, enhanced error handling, advanced caching, and improved intent detection. The design maintains the current architecture while adding robust operational capabilities.

## Architecture

### Current System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │───▶│   FastAPI App    │───▶│  LLM Service    │
│   (web_bot.py)  │    │  (orchestrator)  │    │   (Gemini)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Database Service │
                       │  (JSON + Fuzzy)  │
                       └──────────────────┘
```

### Enhanced Production Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │───▶│   FastAPI App    │───▶│  LLM Service    │
│   (web_bot.py)  │    │  + Middleware    │    │   (Enhanced)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │ Enhanced Cache   │    │ Cost Tracking   │
                    │    (Redis)       │    │    Service      │
                    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │ Database Service │    │   Monitoring    │
                    │  (Enhanced)      │    │    Service      │
                    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │   Logging &      │    │  Health Check   │
                    │ Error Handling   │    │    Endpoints    │
                    └──────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Development Environment Setup

**Component:** Project Infrastructure
- **Virtual Environment:** Python venv with isolated dependencies
- **Dependency Management:** requirements.txt with pinned versions
- **Git Configuration:** .gitignore for Python projects
- **Environment Variables:** .env file for configuration

**Interface:**
```python
# requirements.txt structure
fastapi==0.104.1
uvicorn==0.24.0
google-generativeai==0.3.2
redis==5.0.1
psutil==5.9.6
# ... other dependencies with versions
```

### 2. Cost Tracking Service

**Component:** `CostTrackingService`
- **Token Estimation:** Calculate input/output tokens from text
- **Cost Calculation:** Real-time cost computation based on Gemini pricing
- **Budget Monitoring:** Daily/monthly limit tracking with alerts
- **Reporting:** Export cost data and generate summaries

**Interface:**
```python
class CostTrackingService:
    async def track_api_call(self, service: str, model: str, 
                           input_text: str, output_text: str, 
                           session_id: str, response_time_ms: int) -> float
    
    def get_daily_cost(self, date: Optional[datetime] = None) -> float
    def get_monthly_cost(self, date: Optional[datetime] = None) -> float
    def get_cost_summary(self, hours: int = 24) -> CostSummary
    def get_cost_projection(self) -> Dict[str, float]
```

### 3. Performance Monitoring Service

**Component:** `MonitoringService`
- **Request Tracking:** Response times, status codes, endpoints
- **System Metrics:** CPU, memory, disk usage via psutil
- **Health Assessment:** Status determination based on thresholds
- **Alerting:** Performance warnings and critical alerts

**Interface:**
```python
class MonitoringService:
    async def track_request(self, endpoint: str, method: str, 
                          response_time_ms: int, status_code: int)
    
    def get_system_health(self) -> SystemHealth
    def get_performance_summary(self, hours: int = 24) -> PerformanceSummary
    def get_real_time_metrics(self) -> Dict[str, Any]
```

### 4. Enhanced Error Handling and Logging

**Component:** Structured Logging System
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured Format:** JSON logging with context information
- **Error Context:** Request ID, user session, stack traces
- **Retry Logic:** Exponential backoff for API failures

**Interface:**
```python
class EnhancedLogger:
    def log_request(self, request_id: str, endpoint: str, user_id: str)
    def log_error(self, error: Exception, context: Dict[str, Any])
    def log_performance(self, metric: str, value: float, context: Dict)
    
class RetryHandler:
    async def retry_with_backoff(self, func: Callable, max_retries: int = 3)
```

### 5. Advanced Caching System

**Component:** `EnhancedCacheService`
- **Redis Integration:** Distributed caching with TTL
- **Cache Strategies:** LRU eviction, intelligent invalidation
- **Fallback Mechanism:** Graceful degradation when cache unavailable
- **Cache Warming:** Preload frequently accessed data

**Interface:**
```python
class EnhancedCacheService:
    async def get(self, key: str) -> Optional[Any]
    async def set(self, key: str, value: Any, ttl: int = 3600)
    async def invalidate(self, pattern: str)
    async def get_cache_stats(self) -> CacheStats
```

### 6. Enhanced Intent Detection

**Component:** Improved LLM Service
- **Context-Aware Responses:** Handle ambiguous greetings/farewells
- **Acknowledgment Handling:** Proper responses to "tamam", "ok", etc.
- **Multi-meaning Detection:** "iyi günler" context analysis
- **Conversation Flow:** Maintain context across interactions

**Enhanced Logic:**
```python
# Intent detection improvements
def detect_intent_with_context(self, message: str, context: Dict) -> IntentResult:
    # Handle acknowledgments
    if message.lower() in ["tamam", "ok", "anladım"]:
        return self._handle_acknowledgment(context)
    
    # Handle ambiguous greetings
    if "iyi günler" in message.lower():
        return self._handle_contextual_greeting(message, context)
    
    # Enhanced product search
    if self._is_product_query(message):
        return self._enhanced_product_search(message)
```

### 7. Enhanced Product Search

**Component:** Improved Database Service
- **Turkish Text Normalization:** Handle grammatical cases and variations
- **Semantic Matching:** Better keyword matching with category awareness
- **Scoring Algorithm:** Multi-factor relevance scoring
- **Category Boosting:** Prioritize relevant product categories

**Enhanced Matching:**
```python
def enhanced_product_search(self, query: str) -> List[Product]:
    normalized_query = self._advanced_turkish_normalization(query)
    
    # Multi-factor scoring
    for product in products:
        score = self._calculate_relevance_score(normalized_query, product)
        # Category matching bonus
        # Exact match bonus
        # Keyword coverage bonus
        # Turkish language variations
```

### 8. API Documentation and Validation

**Component:** FastAPI Enhancements
- **OpenAPI Schema:** Automatic API documentation generation
- **Request Validation:** Pydantic models for all endpoints
- **Error Responses:** Structured error messages with details
- **Interactive Docs:** Swagger UI for API testing

**Models:**
```python
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    business_id: str = Field(..., regex="^[a-zA-Z0-9_-]+$")
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    method: str
    confidence: float
    execution_time_ms: int
    cost: Optional[float] = None
```

### 9. Rate Limiting and Security

**Component:** Security Middleware
- **Rate Limiting:** IP-based request throttling
- **Input Sanitization:** Prevent injection attacks
- **Security Headers:** CORS, CSP, security headers
- **Request Validation:** Schema validation and sanitization

**Implementation:**
```python
class SecurityMiddleware:
    def __init__(self, requests_per_minute: int = 60):
        self.rate_limiter = RateLimiter(requests_per_minute)
    
    async def __call__(self, request: Request, call_next):
        # Rate limiting check
        # Input sanitization
        # Security headers
        # Request validation
```

### 10. Health Check System

**Component:** Health Check Endpoints
- **System Health:** CPU, memory, disk status
- **Dependency Health:** External service availability
- **Performance Health:** Response time thresholds
- **Detailed Diagnostics:** Component-level health information

**Endpoints:**
```python
@app.get("/health")
async def health_check() -> HealthResponse

@app.get("/health/detailed")
async def detailed_health() -> DetailedHealthResponse

@app.get("/metrics")
async def metrics() -> MetricsResponse
```

## Data Models

### Cost Tracking Models
```python
@dataclass
class APICall:
    timestamp: str
    service: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    session_id: str
    response_time_ms: int
    success: bool

@dataclass
class CostSummary:
    total_calls: int
    total_cost: float
    avg_cost_per_call: float
    cost_by_service: Dict[str, float]
    cost_projection: Dict[str, float]
```

### Monitoring Models
```python
@dataclass
class SystemHealth:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    response_time_avg: float
    error_rate: float
    status: str  # 'healthy', 'warning', 'critical'

@dataclass
class PerformanceMetric:
    timestamp: str
    metric_type: str
    value: float
    metadata: Dict[str, Any]
```

## Error Handling

### Error Categories
1. **API Errors:** Gemini API failures, rate limits, authentication
2. **System Errors:** Memory issues, disk space, network connectivity
3. **Application Errors:** Invalid requests, business logic failures
4. **Performance Errors:** Timeout, slow responses, resource exhaustion

### Error Response Format
```python
class ErrorResponse(BaseModel):
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]]
    request_id: str
    timestamp: str
    suggested_action: Optional[str]
```

### Retry Strategy
- **Exponential Backoff:** 1s, 2s, 4s, 8s delays
- **Max Retries:** 3 attempts for transient failures
- **Circuit Breaker:** Stop retries after consecutive failures
- **Fallback Responses:** Graceful degradation when services unavailable

## Testing Strategy

### Unit Tests
- **Service Layer:** Individual component testing
- **Cost Calculation:** Token estimation and pricing accuracy
- **Intent Detection:** Various input scenarios
- **Caching Logic:** Cache hit/miss scenarios

### Integration Tests
- **API Endpoints:** Full request/response cycle
- **Error Handling:** Failure scenario testing
- **Performance:** Load testing and stress testing
- **Cost Tracking:** End-to-end cost calculation

### Monitoring Tests
- **Health Checks:** Endpoint availability and response format
- **Performance Metrics:** Metric collection accuracy
- **Alert Thresholds:** Warning and critical alert triggers
- **System Resources:** Resource usage monitoring

### Test Data
- **Mock Responses:** Gemini API response simulation
- **Test Products:** Sample product database for search testing
- **Performance Scenarios:** Various load patterns
- **Error Scenarios:** Different failure modes

## Deployment Considerations

### Environment Setup
- **Virtual Environment:** Isolated Python dependencies
- **Environment Variables:** Configuration via .env files
- **Dependency Management:** Pinned versions in requirements.txt
- **Git Configuration:** Proper .gitignore for Python projects

### Production Requirements
- **Redis Server:** For distributed caching
- **Log Aggregation:** Centralized logging system
- **Monitoring Dashboard:** Grafana or similar for metrics visualization
- **Alert System:** Email/Slack notifications for critical issues

### Scalability
- **Horizontal Scaling:** Multiple FastAPI instances
- **Load Balancing:** Distribute requests across instances
- **Database Optimization:** Connection pooling and query optimization
- **Cache Distribution:** Redis cluster for high availability

This design provides a comprehensive foundation for transforming the current chatbot into a production-ready system while maintaining its existing functionality and adding robust operational capabilities.
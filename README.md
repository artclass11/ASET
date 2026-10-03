# ASET - Advanced Stock Analysis Engine Toolkit

A production-ready, enterprise-grade stock analysis platform with real-time data, technical/fundamental analysis, backtesting, portfolio management, and an interactive dark-themed dashboard.

## 🚀 Features

### Core Analytics
- **Real-time Stock Data**: Powered by yfinance with intelligent caching
- **Technical Analysis**: 50+ indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- **Fundamental Analysis**: P/E ratio, dividend yield, earnings, financial statements
- **Market Screening**: Scan thousands of symbols based on custom criteria
- **Backtesting Engine**: Test strategies on historical data with realistic metrics
- **Portfolio Analytics**: Track holdings, performance, allocation, risk metrics

### Platform Features
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Dark Theme Dashboard**: Streamlit UI with professional dark styling
- **Intelligent Caching**: Redis + SQLite for optimal performance
- **Real-time Alerts**: Price, technical indicator, and portfolio alerts
- **Multi-Market Support**: US, EU, Asia markets with forex and crypto
- **User Authentication**: JWT-based authentication with role-based access
- **Scheduled Jobs**: Celery for background data updates and analysis
- **Observability**: Structured logging, metrics, and monitoring

## 📋 Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: Redis
- **Task Queue**: Celery with Redis broker
- **Data Processing**: Pandas, NumPy, TA-Lib
- **Market Data**: yfinance, polygon.io

### Frontend
- **Dashboard**: Streamlit
- **Visualization**: Plotly
- **UI Framework**: Streamlit-themed components

### DevOps
- **Containerization**: Docker & Docker Compose
- **Web Server**: Gunicorn + Nginx
- **Testing**: pytest, pytest-cov
- **Code Quality**: Black, isort, flake8, mypy

## 🏗️ Project Structure

```
ASET/
├── app/                          # Main application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration management
│   ├── security.py               # Auth & JWT handling
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging setup
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── constants.py          # App constants
│   │   └── types.py              # Type definitions
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py               # Database base classes
│   │   ├── session.py            # Database session management
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── user.py           # User model
│   │       ├── portfolio.py      # Portfolio model
│   │       ├── watchlist.py      # Watchlist model
│   │       ├── alert.py          # Alert model
│   │       ├── backtesting.py    # Backtest result model
│   │       └── stock_data.py     # Cached stock data model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── market_data/
│   │   │   ├── __init__.py
│   │   │   ├── fetcher.py        # Data fetcher (yfinance)
│   │   │   ├── cache.py          # Caching layer
│   │   │   ├── validator.py      # Data validation
│   │   │   └── processor.py      # Data processing
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── technical.py      # Technical indicators
│   │   │   ├── fundamental.py    # Fundamental analysis
│   │   │   ├── patterns.py       # Chart patterns
│   │   │   └── correlations.py   # Correlation analysis
│   │   ├── portfolio/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py        # Portfolio management
│   │   │   ├── metrics.py        # Performance metrics
│   │   │   └── optimizer.py      # Portfolio optimization
│   │   ├── backtest/
│   │   │   ├── __init__.py
│   │   │   ├── engine.py         # Backtest engine
│   │   │   ├── strategies.py     # Strategy definitions
│   │   │   ├── metrics.py        # Backtest metrics
│   │   │   └── reporter.py       # Report generation
│   │   ├── screening/
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py        # Stock screener
│   │   │   ├── filters.py        # Filter definitions
│   │   │   └── rules.py          # Screening rules
│   │   └── alerts/
│   │       ├── __init__.py
│   │       ├── manager.py        # Alert management
│   │       ├── notifier.py       # Notification sender
│   │       └── evaluator.py      # Alert condition evaluator
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py            # API router
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── stocks.py     # Stock endpoints
│   │       │   ├── portfolio.py  # Portfolio endpoints
│   │       │   ├── backtest.py   # Backtest endpoints
│   │       │   ├── alerts.py     # Alert endpoints
│   │       │   ├── screening.py  # Screening endpoints
│   │       │   ├── analysis.py   # Analysis endpoints
│   │       │   ├── users.py      # User endpoints
│   │       │   └── health.py     # Health check endpoints
│   │       └── schemas/
│   │           ├── __init__.py
│   │           ├── stock.py
│   │           ├── portfolio.py
│   │           ├── backtest.py
│   │           ├── alert.py
│   │           └── common.py
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py         # Celery config
│       ├── stock_tasks.py        # Stock data tasks
│       ├── portfolio_tasks.py    # Portfolio tasks
│       ├── alert_tasks.py        # Alert tasks
│       └── scheduled.py          # Scheduled jobs
├── dashboard/                    # Streamlit app
│   ├── __init__.py
│   ├── app.py                    # Main dashboard
│   ├── config.py                 # Dashboard config
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── 1_Dashboard.py        # Main dashboard
│   │   ├── 2_Analysis.py         # Technical analysis
│   │   ├── 3_Portfolio.py        # Portfolio management
│   │   ├── 4_Backtest.py         # Backtesting
│   │   ├── 5_Screening.py        # Market screening
│   │   ├── 6_Alerts.py           # Alert management
│   │   └── 7_Settings.py         # User settings
│   ├── components/
│   │   ├── __init__.py
│   │   ├── charts.py             # Chart components
│   │   ├── tables.py             # Table components
│   │   ├── forms.py              # Form components
│   │   └── theme.py              # Dark theme styling
│   └── utils/
│       ├── __init__.py
│       ├── api_client.py         # API client
│       ├── formatters.py         # Data formatting
│       └── cache.py              # Frontend caching
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/
│   │   ├── test_services/
│   │   │   ├── test_market_data.py
│   │   │   ├── test_analysis.py
│   │   │   ├── test_portfolio.py
│   │   │   └── test_backtest.py
│   │   └── test_utils/
│   │       └── test_helpers.py
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_database.py
│   │   └── test_workflows.py
│   └── e2e/
│       └── test_dashboard.py
├── scripts/
│   ├── __init__.py
│   ├── init_db.py                # Database initialization
│   ├── seed_data.py              # Seed sample data
│   ├── generate_reports.py       # Report generation
│   └── maintenance.py            # Maintenance tasks
├── docker/
│   ├── Dockerfile.backend        # Backend Docker image
│   ├── Dockerfile.dashboard      # Dashboard Docker image
│   ├── Dockerfile.worker         # Worker Docker image
│   └── nginx.conf                # Nginx configuration
├── docker-compose.yml            # Docker Compose setup
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── setup.py                      # Package setup
├── pyproject.toml                # Project configuration
├── pytest.ini                    # Pytest configuration
├── .env.example                  # Environment variables template
├── .github/
│   └── workflows/
│       ├── ci.yml                # CI/CD pipeline
│       └── deploy.yml            # Deployment pipeline
└── docs/
    ├── index.md
    ├── api.md
    ├── deployment.md
    └── contributing.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+ (or use Docker)
- Redis 7+ (or use Docker)

### Development Setup

1. **Clone and setup**
```bash
git clone https://github.com/artclass11/ASET.git
cd ASET
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

4. **Initialize database**
```bash
python scripts/init_db.py
python scripts/seed_data.py
```

5. **Run development server**
```bash
# Terminal 1: FastAPI backend
unicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit dashboard
streamlit run dashboard/app.py

# Terminal 3: Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 4: Celery beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

6. **Access the platform**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## 📚 API Documentation

Full API documentation available at `/docs` when running the backend.

### Key Endpoints

```
POST   /api/v1/auth/login
GET    /api/v1/auth/me
GET    /api/v1/stocks/{symbol}
GET    /api/v1/stocks/{symbol}/historical
GET    /api/v1/stocks/{symbol}/analysis/technical
GET    /api/v1/stocks/{symbol}/analysis/fundamental
GET    /api/v1/portfolio
POST   /api/v1/portfolio/positions
GET    /api/v1/portfolio/performance
POST   /api/v1/backtest
GET    /api/v1/backtest/{test_id}
GET    /api/v1/screening/scan
POST   /api/v1/alerts
GET    /api/v1/alerts
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_services/test_analysis.py

# Run in watch mode
pytest-watch
```

## 📦 Deployment

### Production Deployment

```bash
# Build Docker images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Push to registry
docker push your-registry/aset-backend:latest
docker push your-registry/aset-dashboard:latest

# Deploy to your infrastructure
kubectl apply -f k8s/
```

## 🔧 Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit
3. Run tests: `pytest`
4. Check code quality: `black . && flake8 . && mypy .`
5. Push and create Pull Request

## 📊 Key Services

### Market Data Service
- Fetches real-time and historical data from yfinance
- Caches data in Redis and SQLite
- Automatic cache refresh via scheduled tasks
- Data validation and normalization

### Analysis Service
- 50+ technical indicators
- Fundamental metrics and ratios
- Pattern recognition
- Correlation analysis
- Real-time signal generation

### Portfolio Service
- Position tracking and allocation
- Performance metrics (Sharpe, Sortino, etc.)
- Risk analysis (VaR, beta)
- Rebalancing recommendations
- Tax optimization

### Backtest Engine
- High-performance backtesting
- Multiple strategy templates
- Detailed performance reports
- Walk-forward analysis
- Monte Carlo simulations

## 🔐 Security

- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Environment-based configuration
- Secure password hashing
- API rate limiting
- Input validation and sanitization
- CORS security headers

## 📈 Performance

- Redis caching for market data
- Database query optimization
- Async API endpoints
- Background job processing with Celery
- Efficient data structures and algorithms
- Connection pooling

## 🤝 Contributing

See [CONTRIBUTING.md](docs/contributing.md) for guidelines.

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

For issues and questions:
- GitHub Issues: https://github.com/artclass11/ASET/issues
- Email: support@aset.local
- Docs: https://aset-docs.local

## 🗺️ Roadmap

- [ ] Advanced ML models for prediction
- [ ] Broker API integrations (IB, Alpaca, etc.)
- [ ] Real-time WebSocket updates
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Community strategy marketplace
- [ ] Advanced charting (TradingView integration)
- [ ] Economic calendar integration
- [ ] News sentiment analysis
- [ ] Crypto and forex support expansion

---

**Built with ❤️ for serious traders and analysts**

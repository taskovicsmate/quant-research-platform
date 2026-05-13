# Quant Research Platform

## Overview

Quant Research Platform is a modular quantitative trading research system designed for market data ingestion, data validation, strategy backtesting, machine learning experimentation, and analytics.

The project focuses on building a scalable and reproducible research environment using modern software engineering practices and data engineering principles.

The platform is designed around a clean, service-oriented architecture and supports:

- Historical market data ingestion from cryptocurrency exchanges
- Data validation and ETL pipelines
- Time-series data storage
- Quantitative strategy backtesting
- ML-based trading research
- Experiment tracking
- Analytics and dashboard integration
- Containerized deployment with Docker

The long-term goal of the project is to evolve from a candle-based research platform into a fully event-driven market data and quantitative research system.

---

# Core Features

## Market Data Ingestion

- Historical candle ingestion from Binance API
- Modular market data provider architecture
- Extensible data ingestion pipeline
- Future support for realtime websocket streaming

## ETL Pipeline

- Data validation
- Data normalization
- Missing data handling
- Feature engineering
- Timeframe aggregation
- Technical indicator calculation

## Quantitative Research

- Strategy backtesting
- Parameter optimization
- Performance evaluation
- Trade analytics
- Risk metric calculation

## Machine Learning

- Feature-based ML experimentation
- Structured dataset generation
- Model evaluation
- Experiment tracking with MLflow
- Reproducible training workflows

## Analytics

- Power BI integration
- Strategy comparison dashboards
- Equity curve visualization
- Trade performance analytics

## Infrastructure

- Dockerized services
- PostgreSQL + TimescaleDB
- Modular service architecture
- GitHub-based development workflow

---

# Technology Stack

## Backend

- Python
- FastAPI

## Database

- PostgreSQL
- TimescaleDB

## Data Processing

- Polars
- NumPy

## Quantitative Research

- VectorBT

## Machine Learning

- XGBoost
- MLflow

## Infrastructure

- Docker
- Docker Compose
- Redis

## Analytics

- Power BI

## Development Tools

- Visual Studio Code
- Git
- GitHub

---

# System Architecture

```text
Binance API
      ↓
Market Data Ingestion Service
      ↓
RAW Market Data Storage
      ↓
ETL & Validation Pipeline
      ↓
Processed Market Dataset
      ↓
Backtesting Engine
      ↓
Strategy Results Database
      ↓
ML Pipeline & Experiment Tracking
      ↓
Analytics & Dashboard Layer
```

---

# Project Structure

```text
quant-research-platform/
│
├── services/
│   ├── api-service/
│   ├── etl-service/
│   ├── backtest-service/
│   └── ml-service/
│
├── infrastructure/
│   ├── postgres/
│   └── docker/
│
├── shared/
├── tests/
├── docs/
├── dashboard/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

# Database Architecture

The platform separates market data into multiple logical layers to ensure reproducibility, maintainability, and clean data lineage.

## Schemas

### raw

Stores immutable raw market data received from external providers.

Examples:

- `raw.candles`
- `raw.market_events`

### processed

Stores validated and transformed datasets.

Examples:

- `processed.features`
- `processed.indicators`
- `processed.cleaned_candles`

### backtesting

Stores strategy execution and performance results.

Examples:

- `backtesting.trades`
- `backtesting.strategy_results`
- `backtesting.performance_metrics`

### ml

Stores machine learning related datasets and predictions.

Examples:

- `ml.predictions`
- `ml.training_runs`
- `ml.feature_sets`

---

# Development Roadmap

## Phase 1 — Infrastructure Setup

- Repository initialization
- Docker environment setup
- PostgreSQL + TimescaleDB integration
- FastAPI initialization
- GitHub workflow setup

## Phase 2 — Market Data Ingestion

- Binance historical candle ingestion
- Data provider abstraction layer
- Database persistence
- API endpoints

## Phase 3 — ETL Pipeline

- Data validation
- Data cleaning
- Feature engineering
- Technical indicators
- Aggregation pipelines

## Phase 4 — Backtesting Engine

- VectorBT integration
- RSI strategy
- SMA crossover strategy
- MACD strategy
- Risk metric calculation

## Phase 5 — Machine Learning Pipeline

- Feature dataset generation
- XGBoost experimentation
- Hyperparameter tuning
- MLflow experiment tracking

## Phase 6 — Analytics Dashboard

- Power BI integration
- Strategy performance dashboards
- Trade analytics visualization

## Phase 7 — Realtime Architecture

Future migration from candle-based ingestion toward event-driven realtime market data architecture.

---

# Engineering Goals

The project is intentionally designed around production-oriented engineering principles instead of tutorial-style scripting.

Key engineering goals:

- Modular architecture
- Reproducible workflows
- Clean data lineage
- Scalability
- Maintainability
- Containerized deployment
- Separation of concerns
- Proper experiment tracking
- Quantitative research reproducibility

---

# Future Improvements

## Planned Features

- Websocket-based realtime ingestion
- Tick-level aggregation engine
- Order book analytics
- Advanced feature engineering
- Distributed processing
- Cloud deployment on AWS
- CI/CD pipelines
- Monitoring and alerting
- Multi-exchange support

---

# Local Development

## Prerequisites

- Docker Desktop
- Python 3.12+
- Git
- Visual Studio Code

## Clone Repository

```bash
git clone https://github.com/your-username/quant-research-platform.git
cd quant-research-platform
```

## Environment Variables

Create a `.env` file based on `.env.example`.

## Start Infrastructure

```bash
docker compose up --build
```

## Access Services

### FastAPI

```text
http://localhost:8000/docs
```

### PostgreSQL

```text
localhost:5432
```

---

# Software Engineering Practices

The project follows modern engineering standards:

- Feature branch workflow
- Structured commit history
- Type hints
- Logging
- Automated testing
- Environment isolation
- Containerized services
- Version-controlled infrastructure

---

# Disclaimer

This project is intended for research and educational purposes only.

It does not provide financial advice, investment recommendations, or guaranteed trading performance.

---

# Author

Developed as a quantitative trading research and data engineering portfolio project focused on modern backend architecture, financial data pipelines, and ML experimentation.

# Market Scanner

A sophisticated market scanner that identifies promising trading opportunities.

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Running the Scanner

Run the market scanner:
```bash
python run_scanner.py
```

## Configuration

The scanner uses default configuration values that can be modified in:
`trading_platform/application/config/config.py`

Key parameters:
- Minimum volume: 1,000,000
- Price range: $5 - $1,000
- Volatility range: 15% - 50%
- Momentum lookback: 5 days

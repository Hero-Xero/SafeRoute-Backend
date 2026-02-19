# SafeRoute-Backend
School Bus System Backend with Django

## Setup Instructions

### Prerequisites
- Python 3.12.12
- pip and virtualenv

### Installation

1. **Clone the repository**
    ```bash
    git clone <repository-url>
    cd SafeRoute-Backend
    ```

2. **Create and activate virtual environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Start development server**
    ```bash
    python manage.py runserver
    ```

The server will run at `http://127.0.0.1:8000/`

### Environment Variables
Create a `.env` file in the root directory with necessary configuration variables.

### Testing
```bash
python manage.py test
```
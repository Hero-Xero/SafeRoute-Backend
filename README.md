# SafeRoute-Backend
School Bus System Backend with Django

>[!NOTE]
>You are advised to run this on Linux or Windows subsystem for Linux, as there is docker stuff and there will be probably be permission issues

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

2. **Run The Script**
    ```bash
    source setup.sh
    ```

**Congratulations!**, thats it, all you have to do is
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
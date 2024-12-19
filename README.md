# BreakFast - Intermittent Fasting Tracker

A web application to help users track and manage their intermittent fasting journey.

## Project Documentation

- [ERD (Entity-Relationship Diagram)](https://www.figma.com/board/qqzvxxe9iCEMYfNVbwvgyN/Data-Models?node-id=0-1)
- [Functional Requirements](https://docs.google.com/document/d/1DV6WWCnejZmAVOuw6akC09BRsfU16NbXf_fcyNanCGo/edit?tab=t.0#heading=h.4vgbmyqm0jjv)
- [UI Design (Figma)](https://www.figma.com/design/REzIxWyFfkasWo8my2b2Vj/IM2?node-id=0-1&t=xS0XMfNtj8F2CJBZ-1)

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/JivSTuban/unfinished.git
   cd breakfast
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser (admin account):
   ```bash
   python manage.py createsuperuser
   ```

### Running the Application

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Open your web browser and navigate to:
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Development

To make changes to the database models:
1. Modify the models in `BreakFast_app/models.py`
2. Create migrations:
   ```bash
   python manage.py makemigrations
   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```

## Testing

To run tests:
1. Ensure all dependencies are installed.
2. Run the tests using the following command:
   ```bash
   python manage.py test
   ```

## Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Additional Resources

- [`.gitignore` file](./.gitignore)
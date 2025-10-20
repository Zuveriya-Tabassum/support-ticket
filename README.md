```markdown
 Customer Support Ticketing System – Web Application

 Overview
This web application enables customers to raise support tickets, track their status, and allows support teams to efficiently view, assign, and resolve tickets. Built during an internship at Flipkart Pvt Ltd, the project develops skills in database design, backend APIs, and dynamic frontend interfaces.

---

 Objectives
- Develop a secure, user-friendly system for customer and support team ticket management
- Enable real-time ticket tracking and status updates
- Provide admin and analytics tools for efficient support operations

---

 Key Features

 User Portal
- Sign-up/Login: Secure registration and authentication
- Profile Management: Update profile, photo, password
- Submit Tickets: Create support tickets (category, description, priority)
- Ticket History: View current and past tickets, track statuses

 Admin Portal
- Dashboard: View all tickets, filter by status, priority, date, or agent
- Assign Tickets: Allocate tickets to support agents
- Status Updates: Mark tickets as Open, In Progress, Resolved, Closed
- Notes/Responses: Add internal comments, ticket logs

 Reports & Analytics
- Ticket volume and trends over time
- Resolution time statistics
- Agent performance dashboards

---

 Technology Stack

- Frontend: HTML, CSS, JavaScript, Bootstrap/Tailwind
- Backend: Python (Flask or Django)
- Database: MySQL or PostgreSQL
- Version Control: Git, GitHub

---

 Architecture


[User Portal] <---> [Flask/Django APIs] <---> [MySQL/PostgreSQL Database]
       |
    [Admin Portal]

- Modular MVC structure
- RESTful backend APIs
- Secure authentication and session management

---

 Installation


git clone https://github.com/Zuveriya-Tabassum/support-ticket.git
cd support-ticket
python -m venv venv
venv\Scripts\activate     # Windows
or
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
flask db upgrade          # For Flask-Migrate usage
flask run


---

 Usage

- User: 
  Register/login, update profile, submit tickets, track statuses

- Admint:
  Login, view tickets, assign tickets, change statuses, add notes, view analytics

---

 API Endpoints

| Route                  | Method  | Description            |
|------------------------|---------|------------------------|
| /signup                | POST    | Register new user      |
| /login                 | POST    | Authenticate user      |
| /profile               | GET/PUT | View or edit profile   |
| /tickets               | GET/POST| View/submit ticket     |
| /tickets/<id>          | GET/PUT | View/update ticket     |
| /admin/tickets/assign  | POST    | Assign ticket to agent |
| /admin/reports         | GET     | View analytics         |

---

 Known Issues / Limitations

- Notification emails not implemented
- File uploads limited to profile images only
- Role management basic (no advanced permissions)
- Reporting features basic (expandable)

---


 Contact

- Author: Zuveriya Tabassum Shaik
- GitHub: [support-ticket](https://github.com/Zuveriya-Tabassum/support-ticket)
- Email: (tabassumzuveriya@gmail.com)


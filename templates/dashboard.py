{% extends 'main.html' %}

{% block style %}
    .more a{
        color: aliceblue;
        font-size: 12px;
    }
    td{
        color: aliceblue;
    }
    th{
        color: aliceblue;
    }
{% endblock %}

{% block content %}
    <h1>Dashboard</h1>
    <p>Welcome, {{ current_user.name }}!</p>

    <h3>Your Appointments</h3>
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Service ID</th>
                <th>Description</th>
                <th>Scheduled Time</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for appointment in appointments %}
                <tr>
                    <td>{{ appointment.id }}</td>
                    <td>{{ appointment.description }}</td>
                    <td>{{ appointment.scheduled_time }}</td>
                    <td>{{ appointment.status }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
{% endblock %}

from flask import Flask, jsonify, request,g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, PrimaryKeyConstraint, Date, TIMESTAMP, Text
from flask import abort
from werkzeug.exceptions import NotFound
from sqlalchemy.orm import relationship


###########################################
##   FLASK CONFIGS AND INITIALIZATION    ##
###########################################

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = "dfghwenkl4983ufhwjebf8394nvdnv"
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///potterDB"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///potterDB"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum('teacher', 'student', 'admin'), nullable=False)

    # Define relationships
    teacher_classes = relationship('TeacherClass', back_populates='teacher')
    student_classes = relationship('StudentClass', back_populates='student')
    attendances = relationship('Attendance', back_populates='student')
    grades = relationship('Grade', back_populates='student')

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

class Class(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_code = Column(String(10), unique=True, nullable=False)

    # Define relationships
    assignments = relationship('Assignment', back_populates='class_obj')
    teacher_classes = relationship('TeacherClass', back_populates='class_obj')
    student_classes = relationship('StudentClass', back_populates='class_obj')
    attendances = relationship('Attendance', back_populates='class_obj')

    def __repr__(self):
        return f"<Class(id={self.id}, class_code={self.class_code})>"

class TeacherClass(db.Model):
    teacher_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    class_id = Column(Integer, ForeignKey('class.id'), primary_key=True)

    # Define relationships
    teacher = relationship('User', back_populates='teacher_classes')
    class_obj = relationship('Class', back_populates='teacher_classes')

    def __repr__(self):
        return f"<TeacherClass(teacher_id={self.teacher_id}, class_id={self.class_id})>"


class StudentClass(db.Model):
    student_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    class_id = Column(Integer, ForeignKey('class.id'), primary_key=True)

    # Define relationships
    student = relationship('User', back_populates='student_classes')
    class_obj = relationship('Class', back_populates='student_classes')

    def __repr__(self):
        return f"<StudentClass(student_id={self.student_id}, class_id={self.class_id})>"


class Assignment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    due_date = Column(TIMESTAMP)
    class_id = Column(Integer, ForeignKey('class.id'))

    # Define relationships
    class_obj = relationship('Class', back_populates='assignments')
    grades = relationship('Grade', back_populates='assignment')

    def __repr__(self):
        return f"<Assignment(id={self.id}, title={self.title}, class_id={self.class_id})>"

class Attendance(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('class.id'))
    date = Column(Date)
    student_id = Column(Integer, ForeignKey('user.id'))
    status = Column(Enum('present', 'absent'), nullable=False)

    # Define relationships
    class_obj = relationship('Class', back_populates='attendances')
    student = relationship('User', back_populates='attendances')

    def __repr__(self):
        return f"<Attendance(id={self.id}, class_id={self.class_id}, student_id={self.student_id}, status={self.status})>"

class Grade(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    student_id = Column(Integer, ForeignKey('user.id'))
    score = Column(Float, nullable=False)

    # Define relationships
    assignment = relationship('Assignment', back_populates='grades')
    student = relationship('User', back_populates='grades')

    def __repr__(self):
        return f"<Grade(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id}, score={self.score})>"

#login and authentication routed
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def before_request():
    g.user = current_user


###########################################################
#   LOGIN AND LOGOUT
##########################################################
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.password_hash == password:
        login_user(user)
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200



@app.route('/api/profile')
@login_required
def profile():
    # Print assigned classes for debugging
    print("Assigned Classes:", current_user.teacher_classes)
    return jsonify({"username": current_user.username, "role": current_user.role})
##########################################################
#              API CALLS CRUD                            #
#########################################################
###########


#FOR USER AKA STUDENT/TEACHER
# SINGLE USER CREATION

@app.route('/api/create_user', methods=['POST'])
@login_required
def create_user():
    print(current_user.role)
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        abort(400, {"error": "Username already exists"})

        
    if current_user.role != 'admin':
        # Teachers can only create students
        if role != 'student':
            abort(403, {"error": "Permission denied. Teachers can only create students."})

    # If the current user is an admin, allow creating any role
    if role == 'teacher' and current_user.role != 'admin':
        abort(403, {"error": "Permission denied. Only admins can create teachers."})


    new_user = User(username=username, password_hash=password, full_name=full_name, role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

# MANY USER CREATIONS
#Require a role privilage refactoring

@app.route('/api/create_users', methods=['POST'])
def create_users():
    data = request.get_json()

    users_to_create = data.get('users', [])

    for user_data in users_to_create:
        username = user_data.get('username')
        password = user_data.get('password')
        full_name = user_data.get('full_name')
        role = user_data.get('role')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            abort(400, {"error": f"Username '{username}' already exists"})

        new_user = User(username=username, password_hash=password, full_name=full_name, role=role)
        db.session.add(new_user)

    db.session.commit()

    return jsonify({"message": "Users created successfully"}), 201


#get all users


@app.route('/api/get_users', methods=['GET'])
def get_users():
    users = User.query.all()

    user_list = []
    for user in users:
        user_info = {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role
        }
        user_list.append(user_info)

    return jsonify({"users": user_list})



#################################################
#       CRUD FOR CLASSES ALL API CALLS
################################################

#gett all
@app.route('/api/classes', methods=['GET'])
@login_required
def get_classes():
    if current_user.role == 'admin' or current_user.role == 'teacher':
        classes = Class.query.all()
        return jsonify({'classes': [c.__repr__() for c in classes]}), 200
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can view classes."})

# GET SPECIFIC
@app.route('/api/classes/<int:class_id>', methods=['GET'])
@login_required
def get_class(class_id):
    class_instance = Class.query.get(class_id)
    if class_instance:
        if current_user.role == 'admin' or current_user.role == 'teacher':
            return jsonify(class_instance.__repr__())
        else:
            abort(403, {"error": "Permission denied. Only admins and teachers can view classes."})
    else:
        abort(404, {"error": "Class not found."})


#POST ONE
@app.route('/api/classes', methods=['POST'])
@login_required
def create_class():
    if current_user.role == 'admin' or current_user.role == 'teacher':
        data = request.get_json()
        class_code = data.get('class_code')

        new_class = Class(class_code=class_code)
        db.session.add(new_class)
        db.session.commit()

        return jsonify({"message": "Class created successfully"}), 201
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can create classes."})

#EDIT ONE SPECIFIC
@app.route('/api/classes/<int:class_id>', methods=['PUT'])
@login_required
def update_class(class_id):
    if current_user.role == 'admin' or current_user.role == 'teacher':
        class_instance = Class.query.get(class_id)
        if class_instance:
            data = request.get_json()
            class_instance.class_code = data.get('class_code')
            db.session.commit()

            return jsonify({"message": "Class updated successfully"})
        else:
            abort(404, {"error": "Class not found."})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can update classes."})

#DELETE CLASS
@app.route('/api/classes/<int:class_id>', methods=['DELETE'])
@login_required
def delete_class(class_id):
    if current_user.role == 'admin' or current_user.role == 'teacher':
        class_instance = Class.query.get(class_id)
        if class_instance:
            db.session.delete(class_instance)
            db.session.commit()

            return jsonify({"message": "Class deleted successfully"})
        else:
            abort(404, {"error": "Class not found."})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can delete classes."})



######################################################
        

##########################################################
#              API CALLS FOR ASSIGNMENTS                #
##########################################################
# CREATE Assignment
@app.route('/api/assignments', methods=['POST'])
@login_required
def create_assignment():
    if current_user.role == 'admin' or current_user.role == 'teacher':
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date_str = data.get('due_date')
        class_id = data.get('class_id')

        # Convert the string to a datetime object
        due_date = datetime.fromisoformat(due_date_str)


        new_assignment = Assignment(title=title, description=description, due_date=due_date, class_id=class_id)
        db.session.add(new_assignment)
        db.session.commit()

        return jsonify({"message": "Assignment created successfully"}), 201
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can create assignments."})



@app.route('/api/assignments', methods=['GET'])
@login_required
def get_assignments():
    if current_user.role == 'admin' or current_user.role == 'teacher':
        assignments = Assignment.query.all()
        assignment_list = [{'id': a.id, 'title': a.title, 'description': a.description, 'due_date': a.due_date, 'class_id': a.class_id} for a in assignments]
        return jsonify({'assignments': assignment_list})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can view assignments."})

# READ Specific Assignment
@app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
@login_required
def get_assignment(assignment_id):
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        abort(404, {"error": "Assignment not found."})

    if current_user.role == 'admin' or current_user.role == 'teacher':
        return jsonify({'id': assignment.id, 'title': assignment.title, 'description': assignment.description, 'due_date': assignment.due_date, 'class_id': assignment.class_id})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can view assignments."})

# UPDATE Assignment
@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    if current_user.role == 'admin' or current_user.role == 'teacher':
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404, {"error": "Assignment not found."})

        data = request.get_json()
        assignment.title = data.get('title', assignment.title)
        assignment.description = data.get('description', assignment.description)
        assignment.due_date = data.get('due_date', assignment.due_date)
        assignment.class_id = data.get('class_id', assignment.class_id)

        db.session.commit()

        return jsonify({"message": "Assignment updated successfully"})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can update assignments."})

# DELETE Assignment
@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    if current_user.role == 'admin' or current_user.role == 'teacher':
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            abort(404, {"error": "Assignment not found."})

        db.session.delete(assignment)
        db.session.commit()

        return jsonify({"message": "Assignment deleted successfully"})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can delete assignments."})


###############################################################################################
#           CRUD FOR ATTENDANCE
################################################################################

# GET all attendance records
@app.route('/api/attendance', methods=['GET'])
@login_required
def get_attendance():
    if current_user.role == 'admin' or current_user.role == 'teacher':
        attendance_records = Attendance.query.all()
        return jsonify({'attendance': [a.__repr__() for a in attendance_records]})
    else:
        abort(403, {"error": "Permission denied. Only admins and teachers can view attendance records."})

# GET specific attendance record
@app.route('/api/attendance/<int:attendance_id>', methods=['GET'])
@login_required
def get_specific_attendance(attendance_id):
    attendance_record = Attendance.query.get(attendance_id)
    if attendance_record:
        if current_user.role == 'admin' or current_user.role == 'teacher':
            return jsonify(attendance_record.__repr__())
        else:
            abort(403, {"error": "Permission denied. Only admins and teachers can view attendance records."})
    else:
        abort(404, {"error": "Attendance record not found."})

# POST attendance record
@app.route('/api/attendance', methods=['POST'])
@login_required
def create_attendance():
    if current_user.role == 'teacher':
        data = request.get_json()
        class_id = data.get('class_id')
        student_id = data.get('student_id')
        date = data.get('date')
        status = data.get('status')
        print(current_user.teacher_classes)

        # Check if the teacher is assigned to the specified class
        assigned_class = TeacherClass.query.filter_by(teacher_id=current_user.id, class_id=class_id).first()
        if not assigned_class:
            abort(403, {"error": "Permission denied. You are not assigned to this class."})

        new_attendance = Attendance(class_id=class_id, student_id=student_id, date=date, status=status)
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({"message": "Attendance record created successfully"}), 201
    else:
        abort(403, {"error": "Permission denied. Only teachers can create attendance records."})

# UPDATE attendance record
@app.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
@login_required
def update_attendance(attendance_id):
    if current_user.role == 'teacher':
        attendance_record = Attendance.query.get(attendance_id)
        if attendance_record:
            data = request.get_json()
            attendance_record.status = data.get('status')
            db.session.commit()

            return jsonify({"message": "Attendance record updated successfully"})
        else:
            abort(404, {"error": "Attendance record not found."})
    else:
        abort(403, {"error": "Permission denied. Only teachers can update attendance records."})

# DELETE attendance record
@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
@login_required
def delete_attendance(attendance_id):
    if current_user.role == 'teacher':
        attendance_record = Attendance.query.get(attendance_id)
        if attendance_record:
            db.session.delete(attendance_record)
            db.session.commit()

            return jsonify({"message": "Attendance record deleted successfully"})
        else:
            abort(404, {"error": "Attendance record not found."})
    else:
        abort(403, {"error": "Permission denied. Only teachers can delete attendance records."})






###########################################
        # Teahc and class assignments
#  STUDNET ASSIGNMENT TO CLASSES        
 ##################################

@app.route('/api/get_classes_and_teachers', methods=['GET'])
@login_required
def get_classes_and_teachers():
    if current_user.role != 'admin':
        abort(403, {"error": "Permission denied. Only admins can view classes and teachers."})

    classes_and_teachers = []

    # Retrieve all classes
    classes = Class.query.all()
    for class_obj in classes:
        class_info = {
            'class_id': class_obj.id,
            'class_code': class_obj.class_code,
            'teachers': []
        }

        # Retrieve teachers assigned to the class
        teacher_assignments = TeacherClass.query.filter_by(class_id=class_obj.id).all()
        for assignment in teacher_assignments:
            teacher_info = {
                'teacher_id': assignment.teacher.id,
                'teacher_username': assignment.teacher.username,
                'teacher_full_name': assignment.teacher.full_name
            }
            class_info['teachers'].append(teacher_info)

        classes_and_teachers.append(class_info)

    return jsonify({"classes_and_teachers": classes_and_teachers})



@app.route('/api/assign_teacher_to_class', methods=['POST'])
@login_required
def assign_teacher_to_class():
    if current_user.role != 'admin':
        abort(403, {"error": "Permission denied. Only admins can assign teachers to classes."})

    data = request.get_json()
    teacher_id = data.get('teacher_id')
    class_id = data.get('class_id')

    # Check if both teacher and class exist
    teacher = User.query.get(teacher_id)
    class_obj = Class.query.get(class_id)

    if not teacher or not class_obj:
        abort(404, {"error": "Teacher or class not found."})

    # Check if the teacher is already assigned to the class
    if TeacherClass.query.filter_by(teacher_id=teacher_id, class_id=class_id).first():
        return jsonify({"message": "Teacher already assigned to the class."})

    # Assign the teacher to the class
    new_assignment = TeacherClass(teacher=teacher, class_obj=class_obj)
    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({"message": "Teacher assigned to the class successfully."})


@app.route('/api/assign_student_to_class', methods=['POST'])
@login_required
def assign_student_to_class():
    if current_user.role != 'admin':
        abort(403, {"error": "Permission denied. Only admins can assign students to classes."})

    data = request.get_json()
    student_id = data.get('student_id')
    class_id = data.get('class_id')

    # Add logic to check if the student and class exist

    # Create a new record in the StudentClass table
    new_student_class = StudentClass(student_id=student_id, class_id=class_id)
    db.session.add(new_student_class)
    db.session.commit()
    return jsonify({"message": "Student assigned to class successfully"}), 201


@app.route('/api/get_students_and_classes', methods=['GET'])
@login_required
def get_students_and_classes():
    if current_user.role != 'admin':
        abort(403, {"error": "Permission denied. Only admins can access this information."})

    # Query all students and their assigned classes
    students = User.query.filter_by(role='student').all()

    student_info = []
    for student in students:
        assigned_classes = []
        student_classes = StudentClass.query.filter_by(student_id=student.id).all()
        for student_class in student_classes:
            class_info = {
                "class_id": student_class.class_obj.id,
                "class_code": student_class.class_obj.class_code
            }
            assigned_classes.append(class_info)

        student_data = {
            "id": student.id,
            "full_name": student.full_name,
            "role": student.role,
            "username": student.username,
            "assigned_classes": assigned_classes
        }
        student_info.append(student_data)

    return jsonify({"students": student_info})



##############################################################33






@app.route('/api/hello')
def hello():
    return jsonify(message = 'hellow Word')

 
if __name__ == '__main__':
    app.run(debug=True)
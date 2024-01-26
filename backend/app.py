from flask import Flask, jsonify, request,g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, PrimaryKeyConstraint, Date, TIMESTAMP, Text
from flask import abort


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

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

class Class(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_code = Column(String(10), unique=True, nullable=False)

    def __repr__(self):
        return f"<Class(id={self.id}, class_code={self.class_code})>"

class Assignment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    due_date = Column(TIMESTAMP)
    class_id = Column(Integer, ForeignKey('class.id'))

    def __repr__(self):
        return f"<Assignment(id={self.id}, title={self.title}, class_id={self.class_id})>"

class Attendance(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('class.id'))
    date = Column(Date)
    student_id = Column(Integer, ForeignKey('user.id'))
    status = Column(Enum('present', 'absent'), nullable=False)

    def __repr__(self):
        return f"<Attendance(id={self.id}, class_id={self.class_id}, student_id={self.student_id}, status={self.status})>"

class Grade(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    student_id = Column(Integer, ForeignKey('user.id'))
    score = Column(Float, nullable=False)

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
        return jsonify({'classes': [c.__repr__() for c in classes]})
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
        





@app.route('/api/hello')
def hello():
    return jsonify(message = 'hellow Word')

 
if __name__ == '__main__':
    app.run(debug=True)
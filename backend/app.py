from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, PrimaryKeyConstraint, Date, TIMESTAMP, Text


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




########################################################
#     dababase    TABLE CLASSES                        #
#######################################################
class User(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum('teacher', 'student'), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Class(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_code = Column(String(10), unique=True, nullable=False)

    def __repr__(self):
        return f"<Class(id={self.id}, class_code={self.class_code})>"

class TeacherClass(db.Model):
    __tablename__ = 'teacher_class'

    teacher_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    class_id = Column(Integer, ForeignKey('class.id'), primary_key=True)

    def __repr__(self):
        return f"<TeacherClass(teacher_id={self.teacher_id}, class_id={self.class_id})>"      

class StudentClass(db.Model):
    __tablename__ = 'student_class'

    student_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    class_id = Column(Integer, ForeignKey('class.id'), primary_key=True)

    def __repr__(self):
        return f"<StudentClass(student_id={self.student_id}, class_id={self.class_id})>"

class Assignment(db.Model):
    __tablename__ = 'assignment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    due_date = Column(TIMESTAMP)
    class_id = Column(Integer, ForeignKey('class.id'))

    def __repr__(self):
        return f"<Assignment(id={self.id}, title={self.title}, class_id={self.class_id})>"


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('class.id'))
    date = Column(Date)
    student_id = Column(Integer, ForeignKey('user.id'))
    status = Column(Enum('present', 'absent'), nullable=False)

    def __repr__(self):
        return f"<Attendance(id={self.id}, class_id={self.class_id}, student_id={self.student_id}, status={self.status})>"


class Grade(db.Model):
    __tablename__ = 'grade'

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_id = Column(Integer, ForeignKey('assignment.id'))
    student_id = Column(Integer, ForeignKey('user.id'))
    score = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Grade(id={self.id}, assignment_id={self.assignment_id}, student_id={self.student_id}, score={self.score})>"


##########################################################
#              API CALLS CRUD                            #
#########################################################

#FOR USER AKA STUDENT/TEACHER


@app.route('/api/create_users', methods=['POST'])
def create_user():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')

    new_user = User(username=username, password_hash=password, full_name=full_name, role=role)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201



@app.route('/api/hello')
def hello():
    return jsonify(message = 'hellow Word')

 
if __name__ == '__main__':
    app.run(debug=True)
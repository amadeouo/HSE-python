import csv
from pathlib import Path

from sqlalchemy import Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


BASE_DIR = Path(__file__).resolve().parent


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_name: Mapped[str] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String)
    faculty: Mapped[str] = mapped_column(String)
    course: Mapped[str] = mapped_column(String)
    grade: Mapped[int] = mapped_column(Integer)


class StudentRepository:
    def __init__(self, engine):
        self.engine = engine

    def add_student(self, last_name, first_name, faculty, course, grade):
        with Session(self.engine) as session:
            student = Student(
                last_name=last_name,
                first_name=first_name,
                faculty=faculty,
                course=course,
                grade=grade,
            )
            session.add(student)
            session.commit()
            return student.id

    def load_from_csv(self, file_path):
        with open(file_path, encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            with Session(self.engine) as session:
                count = 0
                for row in reader:
                    session.add(Student(
                        last_name=row["Фамилия"],
                        first_name=row["Имя"],
                        faculty=row["Факультет"],
                        course=row["Курс"],
                        grade=int(row["Оценка"]),
                    ))
                    count += 1
                session.commit()
                return count

    def get_students_by_faculty(self, faculty):
        with Session(self.engine) as session:
            query = (
                select(Student.last_name, Student.first_name)
                .where(Student.faculty == faculty)
                .distinct()
                .order_by(Student.last_name, Student.first_name)
            )
            return [tuple(row) for row in session.execute(query)]

    def get_unique_courses(self):
        with Session(self.engine) as session:
            query = select(Student.course).distinct().order_by(Student.course)
            return list(session.scalars(query))

    def get_students_below_30(self, course):
        with Session(self.engine) as session:
            query = (
                select(Student.last_name, Student.first_name)
                .where(Student.course == course, Student.grade < 30)
                .distinct()
                .order_by(Student.last_name, Student.first_name)
            )
            return [tuple(row) for row in session.execute(query)]

    def get_average_grade_by_faculty(self, faculty):
        with Session(self.engine) as session:
            query = select(func.avg(Student.grade)).where(Student.faculty == faculty)
            return session.scalar(query)


def main():
    engine = create_engine(f"sqlite:///{BASE_DIR / 'students.db'}")
    Base.metadata.create_all(engine)
    repository = StudentRepository(engine)

    with Session(engine) as session:
        count = session.scalar(select(func.count()).select_from(Student))
    if count == 0:
        count = repository.load_from_csv(BASE_DIR / "students.csv")
        print("Загружено записей:", count)

    print("Студенты РЭФ:", repository.get_students_by_faculty("РЭФ"))
    print("Уникальные курсы:", repository.get_unique_courses())
    print("Мат. Анализ, оценка ниже 30:", repository.get_students_below_30("Мат. Анализ"))
    print("Средний балл РЭФ:", repository.get_average_grade_by_faculty("РЭФ"))


if __name__ == "__main__":
    main()

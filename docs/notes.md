Это наблюдения уровня задачи: “прочитал 20 страниц”, “понял тему X”, “сложно даётся”, “нужно повторить”.

src/backend/context/course/
  __init__.py

  domain/
    __init__.py

    entities/
      __init__.py
      course.py
      course_task.py
      course_observation.py
      course_task_observation.py

    value_objects/
      __init__.py
      course_status.py
      course_task_status.py
      course_task_priority.py
      course_task_progress.py
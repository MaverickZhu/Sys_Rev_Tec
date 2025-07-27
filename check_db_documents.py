from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./test.db')

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT id, filename FROM documents ORDER BY id'))
        print('Documents in database:')
        for row in result:
            print(f'ID: {row[0]}, Filename: {row[1]}')
except Exception as e:
    print(f'Error: {e}')
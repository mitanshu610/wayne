# import asyncio
#
# import logging
# from utils.sqlalchemy import Base
# from utils.connection_manager import ConnectionManager
# from utils.connection_handler import ConnectionHandler
#
# TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/test_payments"
#
# test_connection_manager = ConnectionManager(db_url=TEST_DB_URL, db_echo=True)
# test_connection_handler = ConnectionHandler(connection_manager=test_connection_manager)
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
#
# async def create_test_tables():
#     """
#     Create all tables defined in Base metadata in the test database.
#     """
#     async with test_connection_handler.session as session:
#         try:
#             # Drop and recreate schema
#             await session.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
#             logger.info("Dropped and recreated schema.")
#
#             await session.run_sync(Base.metadata.create_all)
#             logger.info("Created tables from Base metadata.")
#         except Exception as e:
#             logger.info(f"Error creating tables: {e}")
#         finally:
#             await test_connection_handler.close()
#
# asyncio.run(create_test_tables())

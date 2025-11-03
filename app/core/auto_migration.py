from sqlalchemy import text, inspect
from app.core.database import engine, Base
from config import settings


class AutoMigration:
    def __init__(self):
        self.engine = engine
        self.metadata = Base.metadata

    async def check_and_update_schema(self):
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SHOW TABLES"))
                existing_tables = [row[0] for row in result.fetchall()]

                defined_tables = list(self.metadata.tables.keys())

                for table_name in defined_tables:
                    if table_name not in existing_tables:
                        await self._create_table(conn, table_name)
                    else:
                        await self._check_column_changes(conn, table_name)

                await conn.run_sync(self.metadata.create_all)

            return True

        except Exception as e:
            return False

    async def _create_table(self, conn, table_name):
        try:
            table = self.metadata.tables[table_name]
            await conn.run_sync(lambda sync_conn: table.create(sync_conn))
        except Exception as e:
            pass

    async def _check_column_changes(self, conn, table_name):
        try:
            # 현재 테이블 스키마 조회
            result = await conn.execute(text(f"DESCRIBE {table_name}"))
            existing_columns = {row[0]: row[1] for row in result.fetchall()}

            if table_name in self.metadata.tables:
                table = self.metadata.tables[table_name]

                for column in table.columns:
                    if column.name not in existing_columns:
                        await self._add_column(conn, table_name, column)
                    else:
                        await self._check_column_type_change(
                            conn, table_name, column, existing_columns[column.name]
                        )

                if settings.active_profile in ("local", "test", "production"):
                    protected_columns = {"id", "created_at", "updated_at"}
                    model_column_names = {c.name for c in table.columns}
                    for db_col in existing_columns.keys():
                        if db_col not in model_column_names and db_col not in protected_columns:
                            try:
                                await conn.execute(text(f"ALTER TABLE {table_name} DROP COLUMN `{db_col}`"))
                            except Exception as drop_err:
                                pass
        except Exception as e:
            pass

    async def _add_column(self, conn, table_name, column):
        try:
            column_type = str(column.type.compile(conn.dialect))
            nullable = "NULL" if column.nullable else "NOT NULL"
            default = f"DEFAULT {column.default.arg}" if column.default else ""

            sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type} {nullable} {default}"
            await conn.execute(text(sql))
        except Exception as e:
            pass

    async def _check_column_type_change(self, conn, table_name, column, existing_type):
        try:
            new_type = str(column.type.compile(conn.dialect))
            if new_type.lower() != existing_type.lower():
                pass
        except Exception as e:
            pass


auto_migration = AutoMigration()


async def auto_update_schema():
    return await auto_migration.check_and_update_schema()

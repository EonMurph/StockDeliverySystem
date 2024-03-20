DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def get_delivery_table(db, test_data=None):
    if not test_data:
        schedule_query = """
                        SELECT *
                        FROM store_delivery_schedule;
                        """
        return db.execute(schedule_query).fetchall()

    elif test_data == "empty":
        return [[]]
    elif test_data == "simple":
        # source=A and target=C
        #   On day=0 route is A(2)->B(3)->C(available on 4)
        #   On day=1 route is A(2)->B(3)->C(available on 4)
        #   On day=2 route is A(4)->C(available on 5)
        #   On day=3 route is A(4)->C(available on 5)
        #   On day=4 route is A(5)->C(available on 6)
        #   On day=5 route is A(9)->B(10)->C(available on 11)
        #   On day=6 route is A(9)->B(10)->C(available on 11)
        return [
            ['A', 'B', 'Tue'],   # from_store, to_store, day
            ['A', 'C', 'Thu'],
            ['A', 'C', 'Fri'],
            ['B', 'C', 'Wed'],
        ]


def get_delivery_dict(table):
    if table == [()]:
        return [()]

    result = {}
    for to_store, from_store, day in sorted(table, key=lambda d: DAYS_OF_WEEK.index(d[2])):
        if to_store not in result:
            result[to_store] = []
        result[to_store] += [(from_store, DAYS_OF_WEEK.index(day))]

    return result


def get_source_stores(db, product_id):
    source_stores_query = """
            SELECT store_id
            FROM products_in_stores
            WHERE product_id = ?
                AND product_amount > 0;
            """

    return [result["store_id"] for result in db.execute(source_stores_query, (product_id, )).fetchall()]


if __name__ == "__main__":
    import sqlite3
    import os

    DATABASE = os.path.join(os.path.abspath(
        os.path.dirname(os.path.dirname(__file__))), "app.db")
    db = sqlite3.connect(DATABASE,
                         detect_types=sqlite3.PARSE_DECLTYPES
                         )
    db.row_factory = sqlite3.Row
    delivery_table = get_delivery_table(db)
    delivery_dict = get_delivery_dict(delivery_table)
    source_stores = get_source_stores(db, 3)
    print(source_stores)

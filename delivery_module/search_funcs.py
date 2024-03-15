from delivery_setup import DAYS_OF_WEEK, get_delivery_dict, get_delivery_table, get_source_stores


def perform_search(delivery_dict, target_store, source_stores, order_day, debug=False):
    ''' Version of Prim's Algorithm, almost like Prim's run in parallel
        algorithm:
            while not reach target_store
                get fastest_delivery in a single hop to all other stores
            keep running while loop as long as it's updating to get all possible routes'''

    # check if any source stores
    if not source_stores:
        return {}

    product_at_store = {}
    for store in source_stores:
        product_at_store[store] = (0, None)
        # product_at_store[store] = (day_product_received, store_received_from)

    # check if target already has product
    if target_store in source_stores:
        return {target_store: (0, None)}

    search_finished = False
    while not search_finished:
        from_stores = list(product_at_store.keys())
        if debug:
            print(f"Stores that have product {from_stores}")

        for from_store in from_stores:
            # makes sure the earliest day to receive order is the order_day or after
            earliest_day = max(product_at_store[from_store][0], order_day)
            search_finished = True
            if debug:
                print(f"Searching from store {from_store}")

            # check if store delivers
            if from_store not in delivery_dict:
                continue

            deliveries = delivery_dict[from_store]
            if debug:
                print(f"\tDeliveries: {deliveries}")
            for to_store, day in deliveries:
                if debug:
                    tmp_message = f"\t\tDelivery to {to_store} on day {day}, {day+7}, {day+14} ... "
                # checks if day is in the past, if so puts a week in the future until in the future
                if day <= earliest_day:
                    day += 7

                # first check sees if to_store not in product_at_store dict as all stores in all routes must be checked
                # second check sees if to_store[day_product_received] is later than the day in the current delivery route
                if to_store not in product_at_store or product_at_store[to_store][0] > day:
                    product_at_store[to_store] = (day, from_store)
                    if debug:
                        print(
                            f"{tmp_message} => USED \n\t\tCan Deliver to store {to_store} on day {day}")
                    search_finished = False
                else:
                    if debug:
                        print(f"{tmp_message} => IGNORED")

    return product_at_store


if __name__ == "__main__":
    import sqlite3
    import os

    DATABASE = os.path.join(os.path.abspath(
        os.path.dirname(os.path.dirname(__file__))), "app.db")
    db = sqlite3.connect(DATABASE,
                         detect_types=sqlite3.PARSE_DECLTYPES
                         )
    db.row_factory = sqlite3.Row

    delivery_table = get_delivery_table(db, "simple")
    delivery_dict = get_delivery_dict(delivery_table)
    source_stores = get_source_stores(db, 3)

    product_delivery = perform_search(delivery_dict, "C", ["A"], 6)
    print(product_delivery)

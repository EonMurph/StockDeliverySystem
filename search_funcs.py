from delivery_setup import DAYS_OF_WEEK, get_delivery_dict, get_delivery_table, get_source_stores


def perform_search(delivery_dict, target_store, source_stores, order_day, debug=False):
    ''' Version of Prim's Algorithm
        algorithm synopsis:
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

                # first check sees if to_store not in product_at_store dict as all stores in delivery routes must be checked
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


def get_duration(order_day, target_store, delivery_timetable):
    """Return the number of days before a product is available at target_store."""

    if target_store not in delivery_timetable:
        return None
    elif delivery_timetable[target_store][0] == 0:
        return None
    else:
        return delivery_timetable[target_store][0] - order_day + 1


def get_route(target_store, delivery_timetable, debug=False):
    """Generate sequence of deliveries to transfer product to target_store by working backwards through delivery_timetable."""

    # check there is actually a route
    if len(delivery_timetable) == 0 or target_store not in delivery_timetable:
        return ["Sorry, no delivery possible for this product."]

    # check if product already at target store
    # i.e value of delivery_table = {target_store: (0, None)}
    if len(delivery_timetable) == 1:
        return [f"Product available at store {target_store} today."]

    route = []
    store = target_store
    while True:
        day, from_store = delivery_timetable[store]
        if debug:
            print(store, day, from_store)

        if store == target_store:
            route += [f"Product available at store {store} from day {day+1}."]
        if from_store is None:
            route += [f"Product available at store {store} today."]
            break
        else:
            route += [
                f"Product delivered from store {from_store} to store {store} on day {day}."]
        store = from_store

    return route[::-1]


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

    target_store = "C"
    source_stores = ["A"]
    order_day = 0
    delivery_timetable = perform_search(delivery_dict, target_store, source_stores, order_day)
    duration = get_duration(order_day, target_store, delivery_timetable)
    route = get_route(target_store, delivery_timetable)
    print(delivery_timetable)
    print(f"The delivery will take {duration} day(s).")
    for path in route:
        print(path)

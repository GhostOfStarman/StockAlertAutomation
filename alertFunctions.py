import sys
import numpy as np
from PyQt5.QtWidgets import *
from yahoo_fin.stock_info import *
import mysql.connector
from mysql.connector import errorcode
from StockAlertGUI import *


# --------------------------------------------------------------------------------------------------
# CONNECTION FUNCTIONS

def establish_connection():
    try:
        connection = mysql.connector.connect(user='', password='', host='')
        print("Connected!")
        return connection
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Invalid User/Password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database DNE")
        else:
            print(err)
    else:
        connection.close()


def close_connection(connection, cursor):
    connection.close()
    cursor.close()


def close_conn_and_update(connection, cursor):
    connection.commit()
    close_connection(connection, cursor)


# --------------------------------------------------------------------------------------------------
# CALCULATION FUNCTIONS

def percent_change(symbol):
    open_price = get_open_price(symbol)
    current_price = get_current_price(symbol)
    change = ((open_price - current_price) / open_price) * 100.00
    return round(change, 2)


def compare_prices(symbol):
    open_price = get_open_price(symbol)
    current_price = get_current_price(symbol)
    return percent_change(open_price, current_price)


# NOTE: Each row in cursor is a tuple of lists
def is_target_price_met(symbol, cursor):
    cursor.execute("SELECT TGTPRICE FROM StockData.Watchlist WHERE TICKER = " + "'" + symbol + "';")
    target_price = round(float(cursor.fetchall()[0][0]), 2)
    live_price = get_current_price(symbol)
    if live_price <= target_price:
        return 1
    return 0


def is_target_gain_met(symbol, cursor):
    cursor.execute("SELECT TGTPERCENT FROM StockData.Watchlist WHERE TICKER = " + "'" + symbol + "';")
    target_gain = round(float(cursor.fetchall()[0][0]), 2)
    current_gain = percent_change(symbol)
    if current_gain <= target_price:
        return 1
    return 0


# --------------------------------------------------------------------------------------------------
# READING FUNCTIONS

def print_watch_list(order_by):
    conn = establish_connection()
    cursor = conn.cursor()
    query = ""
    if order_by == 0:
        query = "SELECT * FROM StockData.WatchList ORDER BY PRICE ASC;"
    elif order_by == 1:
        query = "SELECT * FROM StockData.WatchList ORDER BY PCTCHANGE;"
    else:
        query = "SELECT * FROM StockData.WatchList;"
    cursor.execute(query)
    for row in cursor:
        print(row)
    close_connection(conn, cursor)


# --------------------------------------------------------------------------------------------------
# DATA FUNCTIONS W/ YAHOO API


def get_ticker_data(symbol):
    return get_quote_data(symbol.upper())


def get_open_price(symbol):
    return float(round(get_ticker_data(symbol.upper()).get('regularMarketOpen'), 2))


def get_current_price(symbol):
    return float(round(get_live_price(symbol.upper()), 2))


# --------------------------------------------------------------------------------------------------
# UPDATE FUNCTIONS

def ticker_price_update(symbol, cursor):
    current_price = str(get_current_price(symbol))
    query = "UPDATE StockData.WatchList SET PRICE = '" + current_price + "' WHERE TICKER = " + "'" + symbol + "';"
    cursor.execute(query)
    gain_change = percent_change(symbol)
    query = "UPDATE StockData.WatchList SET PCTCHANGE = '" + str(
        gain_change) + "' WHERE TICKER = " + "'" + symbol + "';"
    cursor.execute(query)


def update_current_prices(watching):
    conn = establish_connection()
    cursor = conn.cursor()
    for ticker in watching:
        ticker_price_update(ticker, cursor)
    close_conn_and_update(conn, cursor)


def insert_ticker(symbol):
    conn = establish_connection()
    cursor = conn.cursor()
    current_price = str(round(get_live_price(symbol), 2))
    query = "INSERT INTO `StockData`.`WatchList` (`TICKER`, `PRICE`, `PCTCHANGE`, `TGTPRICE`, `TGTPERCENT`) " \
            "VALUES ('" + symbol.upper() + "', '" + current_price + "', '0', '0.00', '0');"
    cursor.execute(query)
    close_conn_and_update(conn, cursor)


def delete_ticker(symbol):
    conn = establish_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM StockData.WatchList WHERE TICKER = " + "'" + symbol.upper() + "';")
    close_conn_and_update(conn, cursor)


def set_target_price(symbol, target_price):
    conn = establish_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE StockData.WatchList SET TGTPRICE = '" + target_price + "' WHERE TICKER = " + "'" + symbol + "';")
    close_conn_and_update(conn, cursor)


def set_target_percent(symbol, target_price):
    conn = establish_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE StockData.WatchList SET TGTPRICE = '" + target_price + "' WHERE TICKER = " + "'" + symbol + "';")
    close_conn_and_update(conn, cursor)

# --------------------------------------------------------------------------------------------------

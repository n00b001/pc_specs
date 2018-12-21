import json
import os
import random
from time import sleep, time
from urllib.parse import urlencode, quote
from urllib.request import urlopen

import pandas as pd
import requests

from main.htmlparser import get_element_by_class

s = requests.session()
s.headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}


def get_table(url, gpu):
    html = s.get(url).content
    df_list = pd.read_html(html, header=0)
    df = df_list[-2]
    if gpu:
        column = "Videocard"
        score = 'G3D Mark'
    else:
        column = "Processor"
        score = 'CPU Mark'
    df = df[~df[column].str.lower().str.endswith('m')]
    df = df[~df[column].str.contains('&')]
    df = df[~df[column].str.contains('\+')]
    df = df[~df[column].str.contains('/')]
    df = df[~df[column].str.contains('\\\\')]
    df = df[~df[column].str.contains(',')]
    df = df[df[score].notnull()]
    return df.drop(["Price (USD)"], axis=1)


def add_price(df, gpu):
    times_per_sec = 0.5
    delay = 1.0 / times_per_sec
    if gpu:
        url = "https://www.amazon.co.uk/s/ref=nb_sb_noss?url=node%3D430524031&field-keywords={}"
    else:
        url = "https://www.amazon.co.uk/s/ref=sr_nr_n_1?fst=as%3Aoff&rh=n%3A430515031%2Ck%3A6700k&keywords={}"
    series = []
    for row in df.itertuples():
        counter = 0
        while True:
            try:
                name = row[1]
                name_without_at = name.split(" @")[0]
                if name_without_at.lower().endswith("m"):
                    break

                # name_plus_quotes = '"' + name + '"'
                query = url.format(quote(name_without_at))
                html = s.get(query).content
                html_str = html.decode('utf8')
                if "noResultsTitle" in html_str:
                    break
                if "We didn't find results" in html_str:
                    break
                if "captcha" in html_str.lower():
                    s.cookies.clear()
                    raise Exception("Uh oh, we've got a captcha...")

                # id = get_element_by_id("resultsCol", str(html))
                prices = get_element_by_class("s-price", html_str, 'span')
                if len(prices) == 0:
                    break

                prices = prices[:3]

                max_price = max(prices)
                min_price = min(prices)
                mode = max(set(prices), key=prices.count)
                average = sum(prices) / len(prices)
                first_price = prices[0]
                print("\nGetting price for: {}\nMode: {}\nAverage: {}\nFirst Price: {}\nMax Price: {}\nMin Price: {}\n"
                      .format(name, mode, average, first_price, max_price, min_price))
                series.append([name, first_price])
                break
            except Exception as e:
                print(e)
                counter += 1
            finally:
                random_sleeper = random.randint(0, 100) / 10.0
                sleep(delay + random_sleeper + counter)

    backup_filename = "backup_{}.csv".format(int(time()))
    df.to_csv(backup_filename)
    if gpu:
        price_df = pd.DataFrame(series, columns=["Videocard", "price"])
        merged_df = pd.merge(df, price_df, on=['Videocard'])
        dropped_df = merged_df[merged_df['price'].notnull()]
        filename = "gpu_df.csv"
    else:
        price_df = pd.DataFrame(series, columns=["Processor", "price"])
        merged_df = pd.merge(df, price_df, on=['Processor'])
        dropped_df = merged_df[merged_df['price'].notnull()]
        filename = "cpu_df.csv"
    dropped_df.to_csv(filename)
    os.remove(backup_filename)
    return dropped_df


def add_price_new(df, gpu):
    # times_per_sec = 5.0
    # delay = 1.0 / times_per_sec
    delay = 0
    url = "https://www.ebuyer.com/{}"
    series = []
    for row in df.itertuples():
        counter = 0
        while True:
            try:
                new_name = str(row[1])
                if not gpu and " @" in new_name:
                    new_name = new_name[0:new_name.index(" @")]
                # name_plus_quotes = '"' + name + '"'
                new_name = new_name.lower().replace(" ", "-")
                query = url.format(quote(new_name))
                html = s.get(query).content
                html_str = html.decode('utf8')
                if "Sorry, we couldn't find any results for" in html_str:
                    break
                if "captcha" in html_str.lower():
                    s.cookies.clear()
                    raise Exception("Uh oh, we've got a captcha...")

                # id = get_element_by_id("resultsCol", str(html))
                prices = get_element_by_class("price", html_str, 'p')
                if len(prices) == 0:
                    break

                # max_price = max(prices)
                # min_price = min(prices)
                # mode = max(set(prices), key=prices.count)
                # average = sum(prices) / len(prices)
                # first_price = prices[0]
                # print("\nGetting price for: {}\nMode: {}\nAverage: {}\nFirst Price: {}\nMax Price: {}\nMin Price: {}\n"
                #       .format(name, mode, average, first_price, max_price, min_price))

                prices = prices[:3]
                max_price = max(prices)
                min_price = min(prices)
                mode = max(set(prices), key=prices.count)
                average = sum(prices) / len(prices)
                first_price = prices[0]
                print("\nGetting price for: {}\nMode: {}\nAverage: {}\nFirst Price: {}\nMax Price: {}\nMin Price: {}\n"
                      .format(str(row[1]), mode, average, first_price, max_price, min_price))

                series.append([str(row[1]), first_price])
                break
            except Exception as e:
                print(e)
                counter += 1
            finally:
                random_sleeper = random.randint(0, 100) / 10.0
                sleep(delay + random_sleeper + counter)

    backup_filename = "backup_{}.csv".format(int(time()))
    df.to_csv(backup_filename)
    if gpu:
        column = "Videocard"
        filename = "gpu_df.csv"
    else:
        column = "Processor"
        filename = "cpu_df.csv"

    price_df = pd.DataFrame(series, columns=[column, "price"])
    merged_df = pd.merge(df, price_df, on=[column])
    dropped_df = merged_df[merged_df['price'].notnull()]
    dropped_df.to_csv(filename)
    # os.remove(backup_filename)
    return dropped_df


def add_price_old(df):
    times_per_sec = 3.0
    delay = 1.0 / times_per_sec
    url = "http://octopart.com/api/v3/parts/search"

    # NOTE: Use your API key here (https://octopart.com/api/register)
    url += "?apikey=02334d67"
    for row in df.itertuples():
        name = row[1]
        print("Getting price for: {}".format(name))

        args = [
            ('q', "graphics card"),
            ('start', 0),
            ('limit', 100)
        ]

        url += '&' + urlencode(args)

        data = urlopen(url).read()
        search_response = json.loads(data)

        # print number of hits
        hits = search_response['hits']
        print("Hits: {}".format(hits))

        # print results
        for result in search_response['results']:
            part = result['item']
            # print matched part
            print("%s - %s" % (part['brand']['name'], part['mpn']))
        sleep(delay - (search_response["msec"] / 1000.0))


def run():
    gpu_needed = input("GPU Requirement?").lower()
    cpu_needed = input("CPU Requirement?").lower()
    df_gpus, df_cpus = load_dataframes()

    sorted_gpus = get_from_requirements(gpu_needed, df_gpus, True)
    sorted_cpus = get_from_requirements(cpu_needed, df_cpus, False)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print("\n")
        print("GPUs: {}".format(sorted_gpus.iloc[0:10]))
        print("\n")
        print("CPUs: {}".format(sorted_cpus.iloc[0:10]))


def get_from_requirements(item_needed, df, gpu):
    if gpu:
        column = "Videocard"
        descriptor = "GPUs"
        metric = "G3D Mark"
    else:
        column = "Processor"
        descriptor = "CPUs"
        metric = "CPU Mark"

    row = df[df[column].str.lower().str.contains(item_needed)]
    amount_matched = len(row.index)
    if amount_matched == 0:
        raise Exception("No {} found with that description!".format(descriptor))
    print("\nFound {} {} that match\n".format(amount_matched, descriptor))
    last_row = row.iloc[-1]
    print("\nSelecting: {}\n".format(last_row))
    good_enough = df[df[metric] >= last_row[metric]]
    sorted_cpus = good_enough.sort_values("bang for buck", ascending=False)
    return sorted_cpus


def add_performance_per_price(df, gpu):
    if gpu:
        df["bang for buck"] = df["G3D Mark"] / df["price"]
        df.to_csv("gpu_df_bang.csv")
    else:
        df["bang for buck"] = df["CPU Mark"] / df["price"]
        df.to_csv("cpu_df_bang.csv")
    return df


def load_dataframes():
    if os.path.exists("gpu_df.csv"):
        df_gpus = pd.read_csv("gpu_df.csv", index_col='Unnamed: 0')
    else:
        urls = ["https://www.videocardbenchmark.net/high_end_gpus.html"]
                # "https://www.videocardbenchmark.net/mid_range_gpus.html"
                # "https://www.videocardbenchmark.net/midlow_range_gpus.html"]
        df_gpus = pd.concat([get_table(x, True) for x in urls])
        df_gpus = add_price(df_gpus, True)
    if os.path.exists("cpu_df.csv"):
        df_cpus = pd.read_csv("cpu_df.csv", index_col='Unnamed: 0')
    else:
        urls = ["https://www.cpubenchmark.net/high_end_cpus.html"]
                # "https://www.cpubenchmark.net/mid_range_cpus.html",
                # "https://www.cpubenchmark.net/midlow_range_cpus.html"]
        df_cpus = pd.concat([get_table(x, False) for x in urls])
        df_cpus = add_price(df_cpus, False)

    if os.path.exists("gpu_df_bang.csv"):
        df_gpus = pd.read_csv("gpu_df_bang.csv", index_col='Unnamed: 0')
    else:
        df_gpus = add_performance_per_price(df_gpus, True)
    if os.path.exists("cpu_df_bang.csv"):
        df_cpus = pd.read_csv("cpu_df_bang.csv", index_col='Unnamed: 0')
    else:
        df_cpus = add_performance_per_price(df_cpus, False)
    return df_gpus, df_cpus

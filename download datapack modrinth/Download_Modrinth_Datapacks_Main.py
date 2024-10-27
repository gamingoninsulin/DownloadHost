import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import csv
import os
import datetime


def download_from_modrinth(datapack_url, save_location, download_folder):
    # Go to the datapack URL
    response = requests.get(datapack_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the article links in the project list
    project_list = soup.find('div', class_='project-list display-mode--list')
    if not project_list:
        raise Exception("Project list not found")

    articles = project_list.find_all('article')
    if not articles:
        raise Exception("No articles found")

    # Get the first a tag with href in each article
    for article in articles:
        a_tag = article.find('a', href=True)
        if a_tag:
            project_url = f"https://modrinth.com{a_tag['href']}"
            break

    # Go to the project URL
    response = requests.get(project_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Navigate to the versions page
    nav_links = soup.find('nav').find_all('a')
    versions_url = f"https://modrinth.com{nav_links[3]['href']}"

    # Go to the versions page
    response = requests.get(versions_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the latest version
    span_versions = soup.find('span', text='Versions').find_next('a', href=True)
    if not span_versions:
        raise Exception("Versions not found")
    versions_page_url = f"https://modrinth.com{span_versions['href']}"

    # Go to the versions page
    response = requests.get(versions_page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Select the Game Versions button and set to first option
    game_versions_btn = soup.find('button', string='Game Versions')
    if game_versions_btn:
        game_versions_btn.click()
        first_option = game_versions_btn.find_next('button')
        if first_option:
            first_option.click()

    # Select the Platform button and choose Datapack
    platform_btn = soup.find('button', string='Platform')
    if platform_btn:
        platform_btn.click()
        datapack_option = platform_btn.find_next('button', string='Datapack')
        if datapack_option:
            datapack_option.click()

    # Find the download link in data-v-8a6c59f2 div
    download_div = soup.find('div', {'data-v-8a6c59f2': True})
    if not download_div:
        raise Exception("Download div not found")

    download_a_tag = download_div.find('a', href=True)
    if not download_a_tag:
        raise Exception("Download link not found")

    download_url = download_a_tag['href']
    if not download_url.startswith("http"):
        download_url = f"https://modrinth.com{download_url}"

    # Download the file
    response = requests.get(download_url)
    full_path = os.path.join(save_location, download_folder)
    os.makedirs(full_path, exist_ok=True)
    filename = os.path.basename(download_url)
    file_path = os.path.join(full_path, filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path


def log_downloaded_files(log_file, downloaded_files):
    with open(log_file, 'w') as log:
        for entry in downloaded_files:
            log.write(
                f"Datapack URL: {entry['datapack_url']}, Authors: {entry['datapack_authors']}, Saved at: {entry['path']}\n")


class ModrinthDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Modrinth Downloader")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Create the layout with frames
        self.save_location_frame = tk.Frame(root)
        self.save_location_frame.pack(pady=10)

        self.csv_file_frame = tk.Frame(root)
        self.csv_file_frame.pack(pady=10)

        # Save location input
        self.save_location_label = tk.Label(self.save_location_frame, text="Save Location:")
        self.save_location_label.pack(side=tk.LEFT, padx=5)

        self.save_location_entry = tk.Entry(self.save_location_frame, width=50)
        self.save_location_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(self.save_location_frame, text="Browse", command=self.browse)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        # CSV file input
        self.csv_file_label = tk.Label(self.csv_file_frame, text="CSV File Location:")
        self.csv_file_label.pack(side=tk.LEFT, padx=5)

        self.csv_file_entry = tk.Entry(self.csv_file_frame, width=50)
        self.csv_file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_csv_button = tk.Button(self.csv_file_frame, text="Browse", command=self.browse_csv)
        self.browse_csv_button.pack(side=tk.LEFT, padx=5)

        # Download button
        self.download_button = tk.Button(root, text="Download", command=self.download)
        self.download_button.pack(pady=20)

        # Status label
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=10)

    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_location_entry.delete(0, tk.END)
            self.save_location_entry.insert(0, folder)

    def browse_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file:
            self.csv_file_entry.delete(0, tk.END)
            self.csv_file_entry.insert(0, file)

    def download(self):
        save_location = self.save_location_entry.get()
        csv_file = self.csv_file_entry.get()
        log_file = os.path.join(save_location, "latest.log")
        downloaded_files = []
        try:
            with open(csv_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    datapack_url = row['datapack_url']
                    download_folder = row['datapack_folder']
                    datapack_authors = row['datapack_authors']
                    download_path = download_from_modrinth(datapack_url, save_location, download_folder)
                    downloaded_files.append({
                        'datapack_url': datapack_url,
                        'datapack_authors': datapack_authors,
                        'path': download_path
                    })
            log_downloaded_files(log_file, downloaded_files)
            self.status_label.config(text="Success!", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = ModrinthDownloader(root)
    root.mainloop()

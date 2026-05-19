import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Загрузка избранного - используем полный абсолютный путь
        self.favorites_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favorites.json")
        print(f"📁 Файл избранного будет сохранён по пути: {self.favorites_file}")
        
        self.favorites = self.load_favorites()

        # GUI элементы
        self.setup_ui()
        self.current_results = []

    def load_favorites(self):
        """Загрузка избранного из JSON файла"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"✅ Загружено {len(data)} пользователей из {self.favorites_file}")
                    return data
            except Exception as e:
                print(f"❌ Ошибка загрузки: {e}")
                return []
        else:
            print(f"ℹ️ Файл {self.favorites_file} не существует, будет создан при первом сохранении")
            return []

    def save_favorites(self):
        """Сохранение избранного в JSON файл с отладочной информацией"""
        try:
            print(f"\n💾 Попытка сохранить {len(self.favorites)} пользователей...")
            print(f"📂 Путь: {self.favorites_file}")
            
            # Убеждаемся, что директория существует
            os.makedirs(os.path.dirname(self.favorites_file), exist_ok=True)
            
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
            
            # Проверяем, что файл создался и не пустой
            if os.path.exists(self.favorites_file):
                file_size = os.path.getsize(self.favorites_file)
                print(f"✅ Файл успешно сохранён! Размер: {file_size} байт")
                
                # Показываем содержимое для проверки
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"📄 Содержимое файла:\n{content[:200]}...")
                
                self.status_var.set(f"✅ Сохранено {len(self.favorites)} пользователей")
                return True
            else:
                print("❌ Файл не был создан!")
                self.status_var.set("❌ Ошибка: файл не создан")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            import traceback
            traceback.print_exc()
            self.status_var.set(f"❌ Ошибка: {str(e)}")
            return False

    def setup_ui(self):
        # Верхняя панель поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Введите имя пользователя GitHub:").pack(side=tk.LEFT, padx=(0, 10))

        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.search_user())

        self.search_button = ttk.Button(search_frame, text="🔍 Найти", command=self.search_user)
        self.search_button.pack(side=tk.LEFT)

        # Кнопка для показа пути к файлу
        self.show_path_button = ttk.Button(search_frame, text="📍 Показать путь к JSON", command=self.show_json_path)
        self.show_path_button.pack(side=tk.RIGHT, padx=5)

        self.fav_view_button = ttk.Button(search_frame, text="⭐ Избранное", command=self.show_favorites)
        self.fav_view_button.pack(side=tk.RIGHT, padx=5)

        # Панель с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Вкладка результатов поиска
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Результаты поиска")

        # Таблица результатов
        columns = ("avatar", "username", "repo_count", "followers", "actions")
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, show="headings", height=15)

        self.results_tree.heading("avatar", text="Аватар")
        self.results_tree.heading("username", text="Username")
        self.results_tree.heading("repo_count", text="Репозитории")
        self.results_tree.heading("followers", text="Подписчики")
        self.results_tree.heading("actions", text="Действие")

        self.results_tree.column("avatar", width=60)
        self.results_tree.column("username", width=150)
        self.results_tree.column("repo_count", width=80)
        self.results_tree.column("followers", width=80)
        self.results_tree.column("actions", width=100)

        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_tree.bind("<Double-1>", self.show_user_details)

        # Вкладка избранного
        self.fav_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fav_frame, text="⭐ Избранные пользователи")

        self.fav_tree = ttk.Treeview(self.fav_frame, columns=("username", "added_date"), show="headings", height=15)
        self.fav_tree.heading("username", text="Username")
        self.fav_tree.heading("added_date", text="Дата добавления")
        self.fav_tree.column("username", width=200)
        self.fav_tree.column("added_date", width=150)

        fav_scrollbar = ttk.Scrollbar(self.fav_frame, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=fav_scrollbar.set)

        self.fav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.fav_tree.bind("<Double-1>", self.show_fav_user_details)

        # Кнопка удаления из избранного
        btn_frame = ttk.Frame(self.fav_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="❌ Удалить из избранного", command=self.remove_favorite).pack()

        # Нижний статус-бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_json_path(self):
        """Показать путь к JSON файлу и его содержимое"""
        full_path = os.path.abspath(self.favorites_file)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            messagebox.showinfo("Информация о JSON файле",
                f"📁 Путь: {full_path}\n\n"
                f"📄 Размер: {os.path.getsize(full_path)} байт\n\n"
                f"📝 Содержимое:\n{content if content else '(файл пуст)'}\n\n"
                f"⭐ В избранном в памяти: {len(self.favorites)} пользователей")
        else:
            messagebox.showwarning("Файл не найден",
                f"Файл ещё не создан.\n\n"
                f"Ожидаемый путь: {full_path}\n\n"
                f"Файл будет создан автоматически при первом добавлении пользователя в избранное.")

    def search_user(self):
        """Поиск пользователя через GitHub API"""
        username = self.search_entry.get().strip()

        if not username:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не может быть пустым!")
            self.status_var.set("Ошибка: поле поиска пустое")
            return

        self.status_var.set(f"Поиск пользователя '{username}'...")
        self.search_button.config(state=tk.DISABLED)
        self.root.update()

        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url)

            if response.status_code == 200:
                user_data = response.json()
                self.display_results([user_data])
                self.status_var.set(f"Найден пользователь: {user_data['login']}")
            elif response.status_code == 404:
                messagebox.showinfo("Не найдено", f"Пользователь '{username}' не найден на GitHub")
                self.status_var.set(f"Пользователь '{username}' не найден")
                self.results_tree.delete(*self.results_tree.get_children())
            else:
                messagebox.showerror("Ошибка API", f"Ошибка {response.status_code}: {response.reason}")
                self.status_var.set("Ошибка при обращении к API")

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка сети", "Нет подключения к интернету")
            self.status_var.set("Ошибка сети")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            self.status_var.set(f"Ошибка: {str(e)}")

        finally:
            self.search_button.config(state=tk.NORMAL)

    def display_results(self, users):
        """Отображение результатов поиска в таблице"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        self.current_results = users

        for user in users:
            username = user.get("login", "N/A")
            repos = user.get("public_repos", 0)
            followers = user.get("followers", 0)

            is_fav = any(fav["username"] == username for fav in self.favorites)
            action = "⭐ Удалить" if is_fav else "➕ Добавить"

            self.results_tree.insert("", tk.END, values=("👤", username, repos, followers, action))

    def add_to_favorites(self, username):
        """Добавление пользователя в избранное с немедленным сохранением"""
        if any(fav["username"] == username for fav in self.favorites):
            messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном")
            return

        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url)

            if response.status_code == 200:
                user_data = response.json()
                favorite = {
                    "username": username,
                    "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user_data": user_data
                }
                self.favorites.append(favorite)
                
                # НЕМЕДЛЕННОЕ СОХРАНЕНИЕ
                success = self.save_favorites()
                
                if success:
                    self.update_favorites_display()
                    self.update_results_actions()
                    messagebox.showinfo("Успех", 
                        f"Пользователь {username} добавлен в избранное!\n\n"
                        f"Файл сохранён: {self.favorites_file}")
                    self.status_var.set(f"Добавлен в избранное: {username}")
                else:
                    messagebox.showerror("Ошибка", "Не удалось сохранить файл!")
            else:
                messagebox.showerror("Ошибка", "Не удалось получить данные пользователя")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")

    def remove_from_favorites(self, username):
        """Удаление пользователя из избранного"""
        self.favorites = [fav for fav in self.favorites if fav["username"] != username]
        self.save_favorites()  # Немедленное сохранение
        self.update_favorites_display()
        self.update_results_actions()
        messagebox.showinfo("Успех", f"Пользователь {username} удален из избранного")
        self.status_var.set(f"Удален из избранного: {username}")

    def update_favorites_display(self):
        """Обновление отображения списка избранного"""
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)

        for fav in self.favorites:
            self.fav_tree.insert("", tk.END, values=(
                fav["username"],
                fav.get("added_date", "Неизвестно")
            ))

    def update_results_actions(self):
        """Обновление кнопок действий в результатах поиска"""
        for item in self.results_tree.get_children():
            values = list(self.results_tree.item(item, "values"))
            if len(values) >= 2:
                username = values[1]
                is_fav = any(fav["username"] == username for fav in self.favorites)
                values[4] = "⭐ Удалить" if is_fav else "➕ Добавить"
                self.results_tree.item(item, values=values)

    def show_favorites(self):
        """Переключение на вкладку избранного"""
        self.update_favorites_display()
        self.notebook.select(self.fav_frame)

    def show_user_details(self, event):
        """Показ детальной информации о пользователе"""
        selection = self.results_tree.selection()
        if not selection:
            return

        values = self.results_tree.item(selection[0], "values")
        if len(values) >= 2:
            username = values[1]
            self.show_details_dialog(username)

    def show_fav_user_details(self, event):
        """Показ детальной информации из избранного"""
        selection = self.fav_tree.selection()
        if not selection:
            return

        values = self.fav_tree.item(selection[0], "values")
        if values:
            username = values[0]
            self.show_details_dialog(username)

    def show_details_dialog(self, username):
        """Диалоговое окно с детальной информацией"""
        user_data = None

        for user in self.current_results:
            if user.get("login") == username:
                user_data = user
                break

        if not user_data:
            for fav in self.favorites:
                if fav["username"] == username:
                    user_data = fav.get("user_data")
                    break

        if not user_data:
            try:
                response = requests.get(f"https://api.github.com/users/{username}")
                if response.status_code == 200:
                    user_data = response.json()
            except:
                pass

        if user_data:
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"Информация о {username}")
            detail_window.geometry("500x600")
            detail_window.resizable(False, False)

            info_frame = ttk.Frame(detail_window, padding="15")
            info_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(info_frame, text=f"👤 {user_data.get('name', 'Не указано')}", font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))

            fields = [
                ("Логин:", user_data.get("login", "N/A")),
                ("ID:", user_data.get("id", "N/A")),
                ("Тип:", user_data.get("type", "N/A")),
                ("Компания:", user_data.get("company", "Не указана")),
                ("Блог:", user_data.get("blog", "Нет")),
                ("Локация:", user_data.get("location", "Не указана")),
                ("Email:", user_data.get("email", "Не указан")),
                ("Репозитории:", user_data.get("public_repos", 0)),
                ("Подписчики:", user_data.get("followers", 0)),
                ("Подписки:", user_data.get("following", 0)),
                ("Создан:", user_data.get("created_at", "N/A")[:10]),
                ("Обновлен:", user_data.get("updated_at", "N/A")[:10]),
                ("GitHub профиль:", user_data.get("html_url", "N/A")),
            ]

            for label, value in fields:
                frame = ttk.Frame(info_frame)
                frame.pack(fill=tk.X, pady=3)
                ttk.Label(frame, text=label, width=15, anchor=tk.W).pack(side=tk.LEFT)
                ttk.Label(frame, text=str(value), wraplength=350, anchor=tk.W).pack(side=tk.LEFT, padx=(5, 0))

            def open_profile():
                import webbrowser
                webbrowser.open(user_data.get("html_url", ""))

            ttk.Button(info_frame, text="🌐 Открыть профиль на GitHub", command=open_profile).pack(pady=15)

            is_fav = any(fav["username"] == username for fav in self.favorites)
            if is_fav:
                ttk.Button(info_frame, text="❌ Удалить из избранного",
                          command=lambda: [self.remove_from_favorites(username), detail_window.destroy()]).pack()
            else:
                ttk.Button(info_frame, text="⭐ Добавить в избранное",
                          command=lambda: [self.add_to_favorites(username), detail_window.destroy()]).pack()

    def remove_favorite(self):
        """Удаление выбранного пользователя из избранного"""
        selection = self.fav_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return

        values = self.fav_tree.item(selection[0], "values")
        if values:
            username = values[0]
            if messagebox.askyesno("Подтверждение", f"Удалить {username} из избранного?"):
                self.remove_from_favorites(username)


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
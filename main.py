import flet as ft
import winsound
import math
import time
import threading
import datetime

def main(page: ft.Page):
    page.title = "To Do List"
    
    # Removed flet_audio due to 'Unknown control: Audio' in base Flet client

    # Soft color palette
    bg_color = "#FCE4EC" # Pastel Pink
    card_color = "#FFFFFF" # Cream White
    accent_color = "#F3E5F5" # Lavender
    glow_color = "#FF8A80"
    
    page.bgcolor = bg_color
    page.padding = 50
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.fonts = {
        "Nunito": "https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800&display=swap"
    }
    page.theme = ft.Theme(font_family="Nunito")

    today_date = datetime.date.today()
    date_str = today_date.strftime("%B %d, %Y")
    day_str = today_date.strftime("%A")

    header_title = ft.Text(
        "Today", 
        size=45, 
        weight=ft.FontWeight.W_800, 
        color="#F06292",
    )
    
    date_subtitle = ft.Text(
        f"{day_str}, {date_str}", 
        size=16, 
        weight=ft.FontWeight.W_600, 
        color="#BA68C8",
    )
    
    active_tasks_text = ft.Text(
        "You hold 0 active tasks",
        size=18,
        color="#78909C",
        weight=ft.FontWeight.W_600,
    )

    progress_bar = ft.ProgressBar(value=0, color="#FF8A80", bgcolor="#F8BBD0", border_radius=10)
    progress_container = ft.Container(content=progress_bar, width=500, padding=ft.padding.symmetric(vertical=10))

    header = ft.Column(
        [
            header_title, 
            date_subtitle,
            ft.Container(height=5),
            active_tasks_text
        ], 
        spacing=0,
        alignment=ft.MainAxisAlignment.START,
    )
    
    header_row = ft.Row([header], width=500, alignment=ft.MainAxisAlignment.START)
    
    tasks_list = ft.Column(spacing=20, width=500, alignment=ft.MainAxisAlignment.START)
    tasks = []

    class TaskCard(ft.Container):
        def __init__(self, task_name, priority):
            super().__init__()
            self.task_name = task_name
            self.priority = int(priority)
            self.completed = False
            self.hovered = False
            
            # Form UI (0.7 opacity = #B2)
            self.bgcolor = "#B2FFFFFF"
            self.border_radius = 25
            self.padding = 20
            self.blur = ft.Blur(20, 20, ft.BlurTileMode.CLAMP) # Glassmorphism blur
            
            # Soft shadow (0.15 opacity = #26)
            self.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=15,
                color="#26FF8A80",
                offset=ft.Offset(0, 5)
            )
            
            self.animate = ft.Animation(300, "ease")
            self.animate_scale = ft.Animation(300, "ease")
            self.animate_offset = ft.Animation(400, "easeInOut")
            self.animate_opacity = ft.Animation(500, "easeOut")
            
            self.scale = 1.0
            self.offset = ft.Offset(0, 0.5) # Starts lower for smooth entry
            self.opacity = 0 # Starts transparent
            
            indicator = "⭐" * self.priority
            
            self.title_text = ft.Text(self.task_name, size=18, weight=ft.FontWeight.BOLD, color="#4E342E")
            self.hearts_text = ft.Text(indicator, size=16)
            
            self.check_btn = ft.IconButton(
                icon=ft.Icons.CIRCLE_OUTLINED, 
                icon_color="#F06292", 
                icon_size=28,
                on_click=self.toggle_complete
            )
            
            self.delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_ROUNDED, 
                icon_color="#E57373", 
                opacity=0.5,
                on_click=self.remove_self
            )
            
            self.content = ft.Row(
                controls=[
                    self.check_btn,
                    ft.Column([self.title_text, self.hearts_text], expand=True, spacing=2),
                    self.delete_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
            
            self.on_hover = self.hover_card

        def did_mount(self):
            # Trigger smooth entry
            self.offset = ft.Offset(0, 0)
            self.opacity = 1
            self.update()

        def hover_card(self, e):
            self.hovered = (e.data == "true")
            if self.hovered:
                self.scale = 1.05
                # 0.3 opacity glow = #4D
                self.shadow = ft.BoxShadow(
                    spread_radius=4,
                    blur_radius=25,
                    color="#4DFF8A80",
                    offset=ft.Offset(0, 8)
                )
                self.delete_btn.opacity = 1.0
            else:
                self.scale = 1.0
                # 0.15 opacity glow = #26
                self.shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color="#26FF8A80",
                    offset=ft.Offset(0, 5)
                )
                self.delete_btn.opacity = 0.5
            self.update()

        def toggle_complete(self, e):
            self.completed = not self.completed
            if self.completed:
                self.title_text.decoration = ft.TextDecoration.LINE_THROUGH
                self.title_text.color = "#804E342E" # 0.5 opacity
                self.check_btn.icon = ft.Icons.CHECK_CIRCLE_ROUNDED
                self.check_btn.icon_color = "#81C784"
                self.bgcolor = "#66F3E5F5" # 0.4 opacity lavender
                show_celebration()
                try:
                    winsound.PlaySound("assets/tick.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                except:
                    pass
            else:
                self.title_text.decoration = ft.TextDecoration.NONE
                self.title_text.color = "#4E342E"
                self.check_btn.icon = ft.Icons.CIRCLE_OUTLINED
                self.check_btn.icon_color = "#F06292"
                self.bgcolor = "#B2FFFFFF" # 0.7 opacity
            self.update()
            update_task_stats()

        def remove_self(self, e):
            self.opacity = 0
            self.offset = ft.Offset(1, 0) # Slide out to right
            self.update()
            time.sleep(0.4) # Wait for animation
            if self in tasks:
                tasks.remove(self)
                tasks_list.controls.remove(self)
                page.update()
                update_task_stats()

    celebration_container = ft.Container(
        content=ft.Text("✨🎉 CELEBRATION! YAY! 🎉✨", size=24, weight=ft.FontWeight.W_800, color="#FF4081"),
        opacity=0,
        animate_opacity=ft.Animation(400, "easeInOut"),
        animate_size=ft.Animation(400, "easeInOut"),
        alignment=ft.Alignment(0, 0),
        height=0
    )
    
    # Try adding a flet.Lottie if supported
    try:
        if hasattr(ft, "Lottie"):
            lottie_anim = ft.Lottie(
                src="https://lottie.host/801a248f-3766-4fba-bb6c-ffdfdfb7b13a/TjOKZf3V2c.json",
                width=150, height=150, repeat=True
            )
            celebration_container.content = ft.Row([lottie_anim, ft.Text("Great Job!", size=24, weight=ft.FontWeight.BOLD, color="#FF4081")], alignment=ft.MainAxisAlignment.CENTER)
    except Exception as e:
        pass

    def show_celebration():
        celebration_container.height = 150 if hasattr(ft, "Lottie") else 50
        celebration_container.opacity = 1
        page.update()
        def hide():
            time.sleep(2)
            celebration_container.opacity = 0
            celebration_container.height = 0
            try:
                page.update()
            except:
                pass
        threading.Thread(target=hide, daemon=True).start()

    confetti_container = ft.Container(
        content=ft.Text("🎊🎊 WONDERFUL! ALL TASKS DONE! 🎊🎊", size=20, weight=ft.FontWeight.BOLD, color="#E91E63"),
        opacity=0,
        animate_opacity=ft.Animation(500, "easeInOut"),
        scale=ft.Scale(0.5),
        animate_scale=ft.Animation(500, "bounceOut"),
        alignment=ft.Alignment(0, 0),
        height=0
    )

    def update_task_stats():
        active_tasks = [t for t in tasks if not t.completed]
        active_count = len(active_tasks)
        total_tasks = len(tasks)
        
        if total_tasks == 0:
            active_tasks_text.value = "You hold 0 active tasks"
            progress_bar.value = 0
        else:
            task_word = "tasks" if active_count != 1 else "task"
            active_tasks_text.value = f"You hold {active_count} active {task_word}"
            progress_bar.value = (total_tasks - active_count) / total_tasks
            
        try:
            active_tasks_text.update()
            progress_bar.update()
        except:
            pass

        if tasks and active_count == 0:
            try:
                winsound.PlaySound("assets/chime.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
            except:
                pass
            confetti_container.opacity = 1
            confetti_container.scale = 1.2
            confetti_container.height = 50
            page.update()
            def hide():
                time.sleep(4)
                confetti_container.opacity = 0
                confetti_container.scale = 0.5
                confetti_container.height = 0
                try:
                    page.update()
                except:
                    pass
            threading.Thread(target=hide, daemon=True).start()

    def add_task_clicked(e):
        if not task_input.value.strip():
            return
        prio = priority_dropdown.value
        new_task = TaskCard(task_input.value.strip(), prio)
        tasks.append(new_task)
        tasks_list.controls.insert(0, new_task)
        task_input.value = ""
        task_input.focus()
        page.update()
        update_task_stats()

    task_input = ft.TextField(
        hint_text="Add a new task...", 
        expand=True,
        border_radius=25,
        bgcolor="#99FFFFFF", # 0.6 opacity
        border_color="#F48FB1",
        color="#4E342E",
        text_size=16,
        on_submit=add_task_clicked
    )
    
    priority_dropdown = ft.Dropdown(
        width=120,
        options=[
            ft.dropdown.Option("1", "1 ⭐"),
            ft.dropdown.Option("2", "2 ⭐"),
            ft.dropdown.Option("3", "3 ⭐"),
        ],
        value="1",
        bgcolor="#99FFFFFF", # 0.6 opacity
        border_radius=25,
        border_color="#F48FB1",
        color="#4E342E",
    )
    
    add_btn = ft.FloatingActionButton(
        icon=ft.Icons.ADD_ROUNDED,
        bgcolor="#F06292",
        on_click=add_task_clicked,
    )

    input_row = ft.Row([task_input, priority_dropdown, add_btn], alignment=ft.MainAxisAlignment.CENTER, width=500)
    
    main_column = ft.Column(
        [
            ft.Container(height=10),
            header_row,
            progress_container,
            ft.Container(height=10),
            input_row,
            ft.Container(height=10),
            celebration_container,
            confetti_container,
            ft.Container(height=10),
            tasks_list
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    
    page.add(main_column)

    # Bobbing floating effect
    def start_floating():
        t = 0
        while True:
            t += 0.2
            for i, card in enumerate(tasks):
                if not card.completed and not card.hovered:
                    # Sine wave small offset
                    wave = math.sin(t + i) * 0.05
                    card.offset = ft.Offset(0, wave)
                    try:
                        card.update()
                    except:
                        pass
            time.sleep(0.1)

    threading.Thread(target=start_floating, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")

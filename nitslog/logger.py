from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout as PTLayout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.document import Document
import json
from datetime import datetime
import os
import subprocess

class TaskLogger:
    def __init__(self):
        self.console = Console()
        self.tasks = []
        self.current_task = ""
        self.load_tasks()
        
    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as f:
                self.tasks = json.load(f)
        except FileNotFoundError:
            self.tasks = []
            
    def save_tasks(self):
        with open('tasks.json', 'w') as f:
            json.dump(self.tasks, f, indent=2)
            
    def create_layout(self):
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )
        return layout
    
    def display_tasks(self):
        task_text = Text()
        for idx, task in enumerate(self.tasks):
            date = task.get('date', '')
            title = task.get('title', '')
            task_text.append(f"{idx + 1}. [{date}] {title}\n")
            
        left_panel = Panel(
            task_text,
            title="Tasks",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        
        instructions = Text()
        instructions.append("Commands:\n\n")
        instructions.append("'n' - New Task\n")
        instructions.append("'v' - View Task\n")
        instructions.append("'e' - Edit Task\n")
        instructions.append("'d' - Delete Task\n")
        instructions.append("'q' - Quit\n\n")
        instructions.append("Editor Controls:\n")
        instructions.append("- Use arrow keys to navigate\n")
        instructions.append("- Type normally to edit\n")
        instructions.append("- Ctrl+S to save\n")
        instructions.append("- Ctrl+Q to quit editor\n")
        
        right_panel = Panel(
            instructions,
            title="Instructions",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        
        layout = self.create_layout()
        layout["left"].update(left_panel)
        layout["right"].update(right_panel)
        
        os.system('cls' if os.name == 'nt' else 'clear')
        self.console.print(layout)

    def interactive_edit(self, initial_text="", title="", mode="add"):
        # Ensure initial_text is a string and handle None case
        if initial_text is None:
            initial_text = ""
        
        buffer = Buffer(
            document=Document(text=initial_text, cursor_position=len(initial_text)),
            multiline=True,
        )

        # Create key bindings
        kb = KeyBindings()
        
        @kb.add('c-q')
        def _(event):
            # When quitting, return the original text to prevent data loss
            event.app.exit(result=initial_text)
            
        @kb.add('c-s')
        def _(event):
            # Save the current buffer content
            event.app.exit(result=buffer.text)

        # Create title bar with mode-specific styling
        if mode == "add":
            title_text = f"[ Adding New Task: {title} ]"
        else:
            title_text = f"[ Editing Task: {title} ]"

        # Create title window
        title_window = Window(
            FormattedTextControl(HTML(f"<b><style bg='blue' fg='white'> {title_text} </style></b>")),
            height=1
        )

        # Create editor window with the existing content
        editor_window = Window(BufferControl(buffer=buffer))

        # Create status bar
        status_bar = Window(
            FormattedTextControl(HTML("<b>Ctrl+S</b> to save  <b>Ctrl+Q</b> to quit")),
            height=1
        )

        # Combine windows in a layout
        layout = PTLayout(
            HSplit([
                title_window,
                editor_window,
                status_bar
            ])
        )
        
        # Create application
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True
        )

        # Run the application and ensure we don't lose data
        try:
            result = app.run()
            # If result is None (unexpected case), return original text
            return result if result is not None else initial_text
        except Exception as e:
            self.console.print(f"[red]Error in editor: {str(e)}[/red]")
            # Return original text in case of error
            return initial_text

    def commit_and_push_changes(self, message):
        try:
            subprocess.run(["git", "add", "tasks.json", "tasks.html"], check=True)
            subprocess.run(["git", "commit", "-m", message], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            self.console.print("\n[green]Changes pushed to GitHub successfully![/green]")
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]Error pushing changes to GitHub: {str(e)}[/red]")

    def add_task(self):
        self.console.print("\n[bold blue]Adding New Task[/bold blue]")
        title = Prompt.ask("Enter task title")
        
        self.console.print("\nEnter task content (Ctrl+S to save, Ctrl+Q to quit):")
        content = self.interactive_edit("", title=title, mode="add")
        
        if content is not None and content.strip():  # Only add if there's content
            task = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'title': title,
                'content': content
            }
            
            self.tasks.append(task)
            self.save_tasks()
            self.generate_html()
            self.commit_and_push_changes("Added new task")
            self.console.print("\n[green]Task added successfully![/green]")
        
        input("\nPress Enter to continue...")

    def edit_task(self):
        if not self.tasks:
            self.console.print("\n[yellow]No tasks to edit![/yellow]")
            input("\nPress Enter to continue...")
            return
            
        task_num = Prompt.ask("\nEnter task number to edit", default="1")
        try:
            task_idx = int(task_num) - 1
            if 0 <= task_idx < len(self.tasks):
                task = self.tasks[task_idx]
                
                self.console.print(f"\n[bold blue]Editing Task {task_num}[/bold blue]")
                
                # Edit title
                new_title = Prompt.ask("Enter new title (press Enter to keep current)", 
                                     default=task['title'])
                
                # Edit content with interactive editor
                # Make sure we pass the existing content
                current_content = task.get('content', '')  # Get existing content with empty string as fallback
                self.console.print("\nEdit content (Ctrl+S to save, Ctrl+Q to quit):")
                new_content = self.interactive_edit(
                    initial_text=current_content,
                    title=new_title,
                    mode="edit"
                )
                
                # Only update if we got valid content back
                if new_content is not None:
                    # Update task while preserving the content if editing was cancelled
                    self.tasks[task_idx].update({
                        'title': new_title,
                        'content': new_content,
                        'date_modified': datetime.now().strftime('%Y-%m-%d')
                    })
                    
                    self.save_tasks()
                    self.generate_html()
                    self.commit_and_push_changes("Edited task")
                    self.console.print("\n[green]Task updated successfully![/green]")
            else:
                self.console.print("[red]Invalid task number![/red]")
        except ValueError:
            self.console.print("[red]Please enter a valid number![/red]")
        
        input("\nPress Enter to continue...")
        
    def view_task(self):
        if not self.tasks:
            self.console.print("\n[yellow]No tasks to view![/yellow]")
            input("\nPress Enter to continue...")
            return
            
        task_num = Prompt.ask("\nEnter task number to view", default="1")
        try:
            task_idx = int(task_num) - 1
            if 0 <= task_idx < len(self.tasks):
                task = self.tasks[task_idx]
                os.system('cls' if os.name == 'nt' else 'clear')
                self.console.print(Panel(
                    f"[bold]{task['title']}[/bold]\n\n{task['content']}",
                    title=f"Task {task_num} - {task['date']}",
                    border_style="blue",
                    box=box.ROUNDED,
                    padding=(1, 2),
                ))
            else:
                self.console.print("[red]Invalid task number![/red]")
        except ValueError:
            self.console.print("[red]Please enter a valid number![/red]")
        
        input("\nPress Enter to continue...")
        
    def delete_task(self):
        if not self.tasks:
            self.console.print("\n[yellow]No tasks to delete![/yellow]")
            input("\nPress Enter to continue...")
            return
            
        task_num = Prompt.ask("\nEnter task number to delete", default="1")
        try:
            task_idx = int(task_num) - 1
            if 0 <= task_idx < len(self.tasks):
                deleted_task = self.tasks.pop(task_idx)
                self.save_tasks()
                self.generate_html()
                self.commit_and_push_changes("Deleted task")
                self.console.print(f"\n[green]Deleted task: {deleted_task['title']}[/green]")
            else:
                self.console.print("[red]Invalid task number![/red]")
        except ValueError:
            self.console.print("[red]Please enter a valid number![/red]")
        
        input("\nPress Enter to continue...")
        
    def generate_html(self):
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task List</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .task { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
                .task-title { font-weight: bold; }
                .task-date { color: #888; }
            </style>
        </head>
        <body>
            <h1>Task List</h1>
        """

        for task in self.tasks:
            html_content += f"""
            <div class="task">
                <div class="task-title">{task['title']}</div>
                <div class="task-date">{task['date']}</div>
                <div class="task-content">{task['content']}</div>
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        with open('tasks.html', 'w') as f:
            f.write(html_content)
        self.console.print("\n[green]HTML file generated successfully![/green]")

    def run(self):
        while True:
            self.display_tasks()
            choice = Prompt.ask("\nEnter command", choices=['n', 'v', 'e', 'd', 'q'])
            
            if choice == 'n':
                self.add_task()
            elif choice == 'v':
                self.view_task()
            elif choice == 'e':
                self.edit_task()
            elif choice == 'd':
                self.delete_task()
            elif choice == 'q':
                break

def main():
    logger = TaskLogger()
    logger.run()
    logger.generate_html()

if __name__ == "__main__":
    main()
import tkinter as tk
from tkinter import filedialog, messagebox
from lark import Lark, exceptions
from ast_builder import AST
from semantic_analyzer import semanticAnalyzer
from assembler import assemblerCode

# --- Configuracion de colores y estilo ---
COLOR_FONDO_APP = "#C1D7AE"    # Verde salvia suave
COLOR_FONDO_BLANCO = "#FFFFFF" 
COLOR_BTN_MORADO = "#B6BDF2"   # Lavanda
COLOR_BTN_AMARILLO = "#FFFFA0" # Amarillo pastel
COLOR_BTN_AZUL = "#7697AB"     # Azul acero
COLOR_TEXTO = "#333333"        # Gris oscuro formal

# --- Establecimiento de fuentes ---
FUENTE_TITULO = ("Arial Black", 32, "normal")  
FUENTE_UI = ("Arial", 11)           
FUENTE_CODIGO = ("Consolas", 11)  
   
class CompiladorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Compilador - Equipo 3")
        self.geometry("900x700")
        self.configure(bg=COLOR_FONDO_APP)
        
        self.init_parser()
        self.crear_interfaz()

    def init_parser(self):
        try:
            with open("grammar.lark", "r", encoding="utf-8") as f:
                grammar = f.read()
            self.parser = Lark(grammar, parser="lalr", transformer=AST())
            self.raw_parser = Lark(grammar, parser="lalr", start='start') 
        except FileNotFoundError:
            messagebox.showerror("Error", "Archivo 'grammar.lark' no encontrado.")
            self.quit()

    def crear_interfaz(self):
        # Titulo
        lbl_titulo = tk.Label(self, text="COMPILER", font=FUENTE_TITULO, 
                              bg=COLOR_FONDO_APP, fg="#5E7D73")
        lbl_titulo.pack(pady=(15, 10))

        # Contenedor superior
        frame_top = tk.Frame(self, bg=COLOR_FONDO_APP)
        frame_top.pack(fill=tk.BOTH, expand=True, padx=40, pady=5)

        # --- Columna izquierda (input) ---
        frame_left = tk.Frame(frame_top, bg=COLOR_FONDO_APP)
        frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(frame_left, text="Enter your code:", font=("Arial", 12, "bold"), 
                 bg=COLOR_FONDO_APP, fg=COLOR_TEXTO, anchor="w").pack(fill=tk.X, pady=(0,5))

        self.editor_texto = tk.Text(frame_left, font=FUENTE_CODIGO, height=14, 
                                    bd=0, highlightthickness=0, bg=COLOR_FONDO_BLANCO)
    
        self.editor_texto.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Boton compile 
        btn_compile = tk.Button(frame_left, text="COMPILE", font=("Arial", 11, "bold"),
                                bg=COLOR_BTN_AZUL, fg="white", relief="flat",
                                cursor="hand2", command=self.compilar_completo)
        btn_compile.pack(pady=10, ipadx=30, ipady=2)


        # --- Columna derecha (botones) ---
        frame_right = tk.Frame(frame_top, bg=COLOR_FONDO_APP)
        frame_right.pack(side=tk.RIGHT, fill=tk.Y, padx=(30, 0))

        frame_mini = tk.Frame(frame_right, bg=COLOR_FONDO_APP)
        frame_mini.pack(pady=(25, 20))

        btn_open = tk.Button(frame_mini, text="Open", bg=COLOR_BTN_MORADO, 
                             font=FUENTE_UI, relief="flat", cursor="hand2", width=10,
                             command=self.abrir_archivo)
        btn_open.pack(pady=3)

        btn_save = tk.Button(frame_mini, text="Save", bg=COLOR_BTN_MORADO, 
                             font=FUENTE_UI, relief="flat", cursor="hand2", width=10,
                             command=self.guardar_archivo)
        btn_save.pack(pady=3)

        # Botones de accion
        tk.Label(frame_right, text="", bg=COLOR_FONDO_APP).pack(pady=5) 

        btn_tree = tk.Button(frame_right, text="Parsing Tree", bg=COLOR_BTN_AMARILLO,
                             font=FUENTE_UI, relief="flat", cursor="hand2", width=18,
                             command=self.ver_parse_tree)
        btn_tree.pack(pady=8)

        btn_asm = tk.Button(frame_right, text="Assembler", bg=COLOR_BTN_AMARILLO,
                            font=FUENTE_UI, relief="flat", cursor="hand2", width=18,
                            command=self.generar_ensamblador)
        btn_asm.pack(pady=8)


        # Contenedor inferior (resultados)
        frame_bottom = tk.Frame(self, bg=COLOR_FONDO_APP)
        frame_bottom.pack(fill=tk.BOTH, expand=True, padx=40, pady=(0, 30))

        tk.Label(frame_bottom, text="RESULTS", font=("Arial", 14, "bold"), 
                 bg=COLOR_FONDO_APP, fg="#333333", anchor="w").pack(fill=tk.X, pady=(0,5))

        self.consola = tk.Text(frame_bottom, font=FUENTE_CODIGO, height=8, 
                               bd=0, highlightthickness=0, bg="#F4F4F4") # Un gris muy clarito para diferenciar
        self.consola.pack(fill=tk.BOTH, expand=True)


    def abrir_archivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos", "*.comp *.txt"), ("Todos", "*.*")])
        if ruta:
            with open(ruta, "r", encoding="utf-8") as f:
                self.editor_texto.delete("1.0", tk.END)
                self.editor_texto.insert(tk.END, f.read())

    def guardar_archivo(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".comp")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.editor_texto.get("1.0", tk.END))

    def compilar_completo(self):
        codigo = self.editor_texto.get("1.0", tk.END).strip()
        self.consola.delete("1.0", tk.END)
        if not codigo: return

        try:
            ast = self.parser.parse(codigo)
            sem = semanticAnalyzer()
            errores = sem.analyze(ast[1])

            if errores:
                self.consola.insert(tk.END, " Errores semánticos:\n")
                for err in errores:
                    self.consola.insert(tk.END, f"- {err}\n")
                return
            
            self.consola.insert(tk.END, " Compilación exitosa!\n\n")
            
            # Generar asm preview
            generador = assemblerCode()
            codigo_asm = generador.transform(ast)
            self.consola.insert(tk.END, "--- Preview Ensamblador ---\n")
            lineas = str(codigo_asm).split('\n')
            preview = "\n".join(lineas[:5]) # Solo las primeras 5 lineas
            self.consola.insert(tk.END, preview + "\n... (Ver completo en botón Assembler)")

        except exceptions.UnexpectedCharacters as e:
            self.consola.insert(tk.END, f" Error léxico!:\n{e}")
        except exceptions.UnexpectedInput as e:
            self.consola.insert(tk.END, f" Error sintáctico!:\n{e}")
        except Exception as e:
            self.consola.insert(tk.END, f" Error general!:\n{e}")

    def ver_parse_tree(self):
        codigo = self.editor_texto.get("1.0", tk.END).strip()
        self.consola.delete("1.0", tk.END)
        if not codigo: return

        try:
            arbol = self.raw_parser.parse(codigo)
            self.consola.insert(tk.END, arbol.pretty())
        except Exception as e:
            self.consola.insert(tk.END, f"Error: {e}")

    def generar_ensamblador(self):
        codigo = self.editor_texto.get("1.0", tk.END).strip()
        self.consola.delete("1.0", tk.END)
        if not codigo: return

        try:
            arbol = self.parser.parse(codigo)
            generador = assemblerCode()
            codigo_asm = generador.transform(arbol)
            self.consola.insert(tk.END, str(codigo_asm))
        except Exception as e:
            self.consola.insert(tk.END, f"Error generando ensamblador: {e}")

if __name__ == "__main__":
    app = CompiladorGUI()
    app.mainloop()

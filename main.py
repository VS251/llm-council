from fastapi import FastAPI
from pydantic import BaseModel
from council import engine_debate
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.markdown import Markdown
import re

console = Console()

def format_consensus_text(text):
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        if not line:
            formatted_lines.append('')
            continue
            
        if line.startswith('##'):
            formatted_lines.append(f"\n{line.replace('##', '').strip().upper()}")
            formatted_lines.append("=" * len(line.replace('##', '').strip()))
        elif line.startswith('###'):
            formatted_lines.append(f"\n{line.replace('###', '').strip()}")
            formatted_lines.append("-" * len(line.replace('###', '').strip()))
        else:
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*', r'\1', line)
            line = re.sub(r'`(.*?)`', r'\1', line)
            line = re.sub(r'```(.*?)```', r'\1', line, flags=re.DOTALL)
            line = line.replace('*', '')
            line = line.replace('`', '')
            
            if original_line.strip().startswith('*') or original_line.strip().startswith('-'):
                bullet_text = line.lstrip('*- ').strip()
                formatted_lines.append(f"  • {bullet_text}")
            elif re.match(r'^\d+\.', original_line.strip()):
                number_text = re.sub(r'^\d+\.\s*', '', line.strip())
                formatted_lines.append(f"  {original_line.strip()}")
            elif line.strip().startswith('//'):
                formatted_lines.append(Text(line, style="grey50"))
            elif any(keyword in line for keyword in ['int ', 'float ', 'char ', 'bool ', 'std::', 'cout', 'cin', '#include']):
                formatted_lines.append(Text(line, style="yellow"))
            else:
                formatted_lines.append(line)
    
    result = '\n'.join(formatted_lines)
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)  
    return result.strip()

def print_engine_report(data):
    console.print("\n")
    
    title = Text("MULTI-MODEL INFERENCE ENGINE", style="bold blue")
    console.print(Panel(title, expand=False))
    
    console.print("\n[bold]Stage 1: Parallel Inference[/bold]")
    stage1_cols = Columns([
        Panel(f"Gemini Response Complete", title="Gemini 2.0 Flash Lite", border_style="blue"),
        Panel(f"Llama Response Complete", title="Llama 3.1", border_style="green")
    ])
    console.print(stage1_cols)
    
    console.print("\n[bold]Stage 2: Peer Reviews[/bold]")
    stage2_cols = Columns([
        Panel(f"Gemini Review Complete", title="Gemini's Review", border_style="blue"),
        Panel(f"Llama Review Complete", title="Llama's Review", border_style="green")
    ])
    console.print(stage2_cols)
    
    console.print("\n[bold]Stage 3: Consensus Synthesis[/bold]")
    formatted_consensus = format_consensus_text(data['consensus'])
    synthesis_panel = Panel(
        formatted_consensus,
        title="Final Consensus",
        border_style="green"
    )
    console.print(synthesis_panel)
    console.print("\n")

app = FastAPI()

class AskRequest(BaseModel):
    question: str

@app.get("/")
def get_status():
    return {"status": "running", "message": "Multi-Model Inference Engine API is online"}

@app.post("/ask")
async def ask_question(request: AskRequest):
    import asyncio
    result = await engine_debate(request.question)
    print_engine_report(result)
    return result

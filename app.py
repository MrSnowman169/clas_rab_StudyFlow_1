from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pathlib import Path
from datetime import datetime
import json, uuid

app=Flask(__name__); app.secret_key="studyflow-local"
DATA=Path(__file__).with_name("study_data.json")
def load():
    if DATA.exists():
        try: return json.loads(DATA.read_text(encoding="utf-8"))
        except Exception: pass
    return {"tasks":[],"settings":{"sound":False,"frequency":"after_task"}}
def save(d): DATA.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
@app.get("/")
def index():
    d=load(); return render_template("index.html",pending=[x for x in d["tasks"] if x["status"]=="pending"],completed=[x for x in d["tasks"] if x["status"]=="completed"],settings=d["settings"])
@app.post("/tasks/add")
def add():
    title=request.form.get("title","").strip()
    try: duration=int(request.form.get("duration",25))
    except: duration=0
    if not title or not 1<=duration<=600: flash("Введіть назву та тривалість від 1 до 600 хв.","error")
    else:
        d=load(); d["tasks"].append({"id":str(uuid.uuid4()),"title":title,"duration":duration,"status":"pending","created_at":datetime.now().isoformat()}); save(d); flash("Завдання додано.","success")
    return redirect(url_for("index"))
@app.post("/tasks/<tid>/edit")
def edit(tid):
    d=load(); t=next((x for x in d["tasks"] if x["id"]==tid),None)
    if t:
        title=request.form.get("title","").strip()
        try: duration=int(request.form.get("duration",t["duration"]))
        except: duration=0
        if title and 1<=duration<=600: t.update(title=title,duration=duration); save(d); flash("Завдання оновлено.","success")
        else: flash("Перевірте назву та тривалість.","error")
    return redirect(url_for("index"))
@app.post("/tasks/<tid>/delete")
def delete(tid):
    d=load(); d["tasks"]=[x for x in d["tasks"] if x["id"]!=tid]; save(d); return redirect(url_for("index"))
@app.post("/tasks/<tid>/restore")
def restore(tid):
    d=load(); t=next((x for x in d["tasks"] if x["id"]==tid),None)
    if t: t["status"]="pending"; t.pop("completed_at",None); save(d)
    return redirect(url_for("index"))
@app.post("/tasks/<tid>/complete")
def complete(tid):
    d=load(); t=next((x for x in d["tasks"] if x["id"]==tid),None)
    if t: t["status"]="completed"; t["completed_at"]=datetime.now().isoformat(); save(d)
    return jsonify(ok=bool(t))
@app.post("/settings")
def settings():
    d=load(); d["settings"]={"sound":request.form.get("sound")=="on","frequency":request.form.get("frequency","after_task")}; save(d); flash("Налаштування збережено.","success"); return redirect(url_for("index"))
@app.get("/api/tasks")
def api_tasks(): return jsonify(load()["tasks"])
if __name__=="__main__": app.run(debug=True)

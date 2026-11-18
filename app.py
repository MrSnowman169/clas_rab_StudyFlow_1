from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pathlib import Path
from datetime import datetime
import json, uuid

app=Flask(__name__); app.secret_key="studyflow-local"
DATA=Path(__file__).with_name("study_data.json")
DAYS=[("Пн","Понеділок"),("Вт","Вівторок"),("Ср","Середа"),("Чт","Четвер"),("Пт","П'ятниця"),("Сб","Субота"),("Нд","Неділя")]

def default_data(): return {"tasks":[],"lists":[],"reminders":[],"settings":{"sound":False,"frequency":"after_task"}}
def load():
    d=default_data()
    if DATA.exists():
        try: d=json.loads(DATA.read_text(encoding="utf-8"))
        except Exception: d=default_data()
    d.setdefault("tasks",[]); d.setdefault("lists",[]); d.setdefault("reminders",[]); d.setdefault("settings",{"sound":False,"frequency":"after_task"})
    for t in d["tasks"]: t.setdefault("list_id",None)
    return d
def save(d): DATA.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
def valid_list(d,lid): return lid if any(l["id"]==lid for l in d["lists"]) else None

@app.get("/")
def index():
    d=load()
    pending=[x for x in d["tasks"] if x["status"]=="pending"]
    completed=[x for x in d["tasks"] if x["status"]=="completed"]
    names={l["id"]:l["name"] for l in d["lists"]}
    groups=[{"id":l["id"],"name":l["name"],"tasks":[t for t in pending if t.get("list_id")==l["id"]]} for l in d["lists"]]
    free=[t for t in pending if not t.get("list_id")]
    existing={l["name"].strip().lower() for l in d["lists"]}
    day_chips=[{"abbr":a,"name":n,"used":n.lower() in existing} for a,n in DAYS]
    reminders=[]
    for r in sorted(d["reminders"],key=lambda x:x.get("due","")):
        try:
            due=datetime.fromisoformat(r.get("due","")); disp=due.strftime("%d.%m.%Y %H:%M"); overdue=due<datetime.now() and not r.get("notified")
        except Exception:
            disp=r.get("due",""); overdue=False
        reminders.append({"id":r.get("id",""),"text":r.get("text",""),"due":r.get("due",""),"due_display":disp,"notified":bool(r.get("notified")),"overdue":overdue})
    return render_template("index.html",pending=pending,completed=completed,lists=d["lists"],groups=groups,free=free,list_names=names,day_chips=day_chips,reminders=reminders,open_list=request.args.get("open",""),settings=d["settings"])

@app.post("/tasks/add")
def add():
    title=request.form.get("title","").strip()
    try: duration=int(request.form.get("duration",25))
    except: duration=0
    target=url_for("index")
    if not title or not 1<=duration<=600: flash("Введіть назву та тривалість від 1 до 600 хв.","error")
    else:
        d=load(); lid=valid_list(d,request.form.get("list_id",""))
        d["tasks"].append({"id":str(uuid.uuid4()),"title":title,"duration":duration,"status":"pending","created_at":datetime.now().isoformat(),"list_id":lid}); save(d); flash("Завдання додано.","success")
        if lid: target=url_for("index",open=lid)
    return redirect(target)

@app.post("/tasks/<tid>/edit")
def edit(tid):
    d=load(); t=next((x for x in d["tasks"] if x["id"]==tid),None)
    if t:
        title=request.form.get("title","").strip()
        try: duration=int(request.form.get("duration",t["duration"]))
        except: duration=0
        if title and 1<=duration<=600:
            t.update(title=title,duration=duration,list_id=valid_list(d,request.form.get("list_id","")))
            save(d); flash("Завдання оновлено.","success")
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

@app.post("/lists/add")
def add_list():
    name=request.form.get("name","").strip()
    d=load()
    if not name: flash("Введіть назву списку.","error")
    elif len(name)>40: flash("Назва списку — до 40 символів.","error")
    elif any(l["name"].strip().lower()==name.lower() for l in d["lists"]): flash("Список «"+name+"» уже існує.","error")
    else:
        d["lists"].append({"id":str(uuid.uuid4()),"name":name}); save(d); flash("Список «"+name+"» створено.","success")
    return redirect(url_for("index"))

@app.post("/lists/<lid>/use")
def use_list(lid):
    d=load(); lst=next((l for l in d["lists"] if l["id"]==lid),None)
    if not lst: flash("Список не знайдено.","error"); return redirect(url_for("index",_anchor="tasks"))
    saved=[t for t in d["tasks"] if t["status"]=="pending" and t.get("list_id")==lid]
    active={(t["title"].strip().lower(),t["duration"]) for t in d["tasks"] if t["status"]=="pending" and not t.get("list_id")}
    added=0
    for t in saved:
        key=(t["title"].strip().lower(),t["duration"])
        if key in active: continue
        d["tasks"].append({"id":str(uuid.uuid4()),"title":t["title"],"duration":t["duration"],"status":"pending","created_at":datetime.now().isoformat(),"list_id":None})
        added+=1
    save(d)
    if added: flash("Зі списку «"+lst["name"]+"» додано у верхній список завдань: "+str(added)+".","success")
    elif saved: flash("Усі завдання зі списку «"+lst["name"]+"» вже є у верхньому списку.","success")
    else: flash("У списку «"+lst["name"]+"» немає завдань.","error")
    return redirect(url_for("index",_anchor="tasks"))

@app.post("/lists/<lid>/delete")
def delete_list(lid):
    d=load()
    active={(t["title"].strip().lower(),t["duration"]) for t in d["tasks"] if t["status"]=="pending" and not t.get("list_id")}
    kept=[]
    for t in d["tasks"]:
        if t.get("list_id")==lid:
            if t["status"]=="pending" and (t["title"].strip().lower(),t["duration"]) in active: continue
            t["list_id"]=None
        kept.append(t)
    d["tasks"]=kept; d["lists"]=[l for l in d["lists"] if l["id"]!=lid]
    save(d); flash("Список видалено, його завдання перенесено до «Без списку».","success")
    return redirect(url_for("index"))

@app.post("/reminders/add")
def add_reminder():
    text=request.form.get("text","").strip()
    raw=request.form.get("due","").strip()
    try: due=datetime.fromisoformat(raw)
    except Exception: due=None
    if not text or due is None: flash("Введіть текст і дату нагадування.","error")
    elif len(text)>120: flash("Текст нагадування — до 120 символів.","error")
    else:
        d=load(); d["reminders"].append({"id":str(uuid.uuid4()),"text":text,"due":due.strftime("%Y-%m-%dT%H:%M"),"notified":False,"created_at":datetime.now().isoformat()}); save(d); flash("Нагадування додано.","success")
    return redirect(url_for("index"))

@app.post("/reminders/<rid>/delete")
def delete_reminder(rid):
    d=load(); d["reminders"]=[r for r in d["reminders"] if r.get("id")!=rid]; save(d); flash("Нагадування видалено.","success")
    return redirect(url_for("index"))

@app.post("/reminders/<rid>/ack")
def ack_reminder(rid):
    d=load(); r=next((x for x in d["reminders"] if x.get("id")==rid),None)
    if r: r["notified"]=True; save(d)
    return jsonify(ok=bool(r))

@app.post("/settings")
def settings():
    d=load(); d["settings"]={"sound":request.form.get("sound")=="on","frequency":request.form.get("frequency","after_task")}; save(d); flash("Налаштування збережено.","success"); return redirect(url_for("index"))
@app.get("/api/tasks")
def api_tasks(): return jsonify(load()["tasks"])
if __name__=="__main__": app.run(debug=True)

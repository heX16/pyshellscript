
p = create_process('some.exe')
p.run()

proc_run('some1.exe')

pipe('some1.exe') >> pipe('some2.exe') >> pipe('some3.exe')

p1 = create_process('some1.exe')
p2 = create_process('some2.exe')
p3 = create_process('some3.exe')
p1 >> p2 >> p3

proc_run_bg('some1.exe')

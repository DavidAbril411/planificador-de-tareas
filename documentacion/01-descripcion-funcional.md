# Descripción funcional

## Problema que resuelve

Un proyecto tiene tareas que dependen unas de otras: algunas no pueden empezar hasta que terminen otras. Hay que decidir en qué orden hacerlas, cuáles pueden ir al mismo tiempo y cuánto va a tardar todo.

## Alcance

El sistema:

- recibe tareas con duración, prioridad y dependencias;
- calcula el orden de ejecución y detecta los ciclos;
- calcula la duración según los recursos disponibles;
- ejecuta las tareas de verdad, con uno o varios procesos;
- guarda y lee archivos grandes de tareas;
- muestra todo en una interfaz web.

Queda fuera del alcance: guardar proyectos entre sesiones, usuarios y permisos, y correr expuesto a internet.

## Requisitos

| Requisito | Descripción |
|---|---|
| Orden | Ninguna tarea va antes de las que necesita |
| Prioridad | Entre las tareas disponibles va primero la de mayor prioridad |
| Ciclos | Si hay un ciclo, se informa el error y no se ejecuta nada |
| Recursos | Nunca corren más tareas que los recursos disponibles |
| Eficiencia | Planificar 2.000 tareas tiene que tardar milisegundos |

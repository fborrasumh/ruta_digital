# Ruta Digital

Plataforma formativa gratuita sobre investigación y persecución de los **delitos de alta tecnología en la República Dominicana**. Un solo caso simulado, recorrido desde las siete sillas del sistema de justicia.

Implementación de la *Especificación funcional v1.0* como aplicación de **un solo archivo**: sin servidor, sin cuenta, sin base de datos. El usuario pone su clave de OpenAI y juega.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | La app completa (HTML + CSS + JS vanilla, sin build, sin dependencias) |
| `conocimiento.json` | *Opcional*. Textos normativos verificados para anclar lo que genera la IA |

## Despliegue

Suba `index.html` a la raíz del repo y active GitHub Pages. Nada más.

Si añade `conocimiento.json` junto al `index.html`, la app lo carga sola con `fetch`. Abierto en local (`file://`) ese `fetch` falla por CORS: cárguelo a mano desde **⚙ Ajustes**, o sirva la carpeta con `python3 -m http.server`.

## Cómo funciona

**Sin cuenta.** El progreso vive en `localStorage` de ese navegador:

| Clave | Contenido |
|---|---|
| `ia_openai_key` | La clave de OpenAI del usuario (compartida con el resto del catálogo de apps) |
| `rutadigital_model` | Modelo elegido, por defecto `gpt-4o-mini` |
| `rutadigital_state_v1` | Rol, día del expediente, niveles diagnosticados, puntuaciones por módulo |

La clave solo viaja a `api.openai.com`. No hay servidor intermedio, ni analítica, ni cookies. «Borrar todo» vacía esas tres claves y no queda rastro en ningún otro sitio, porque nunca lo hubo. Hay exportación e importación del progreso en JSON para cambiar de equipo.

**Todo el contenido se genera en el momento** con `gpt-4o-mini` sobre una plantilla que recibe el caso, el rol, el módulo, el nivel diagnosticado y el día del expediente. Dos participantes nunca reciben el mismo reto: es el control de integridad del capítulo 6.2 llevado al extremo, banco infinito en vez de banco grande.

### Las piezas

- **Diagnóstico adaptativo.** 18 ítems de aplicación en tres dimensiones (conceptos técnicos, marco normativo, decisión procesal). Si falla dos seguidos en una dimensión, deja de subir dificultad. Resultado por dimensión, sin nota global.
- **El reloj del expediente.** Los 90 días del artículo 56 como cronómetro visible en cabecera. Cada reto consume días; cada decisión equivocada consume más. Al pasar del día 90 los prompts cambian: los datos de conexión que no se pidieron ya no existen.
- **Siete rutas** con los módulos de la especificación, y tres motores de reto por módulo:
  - *Decisión en el caso* — qué hace usted ahora, con la consecuencia procesal de cada opción incorrecta.
  - *El documento* — redactar el acta, la solicitud, el informe o la impugnación, corregido con la rúbrica del rol.
  - *Caza el defecto* — un documento del expediente con 5-7 defectos deliberados que hay que encontrar.
- **Vista cruzada.** Desde cualquier módulo completado, el mismo momento del caso visto desde otro asiento.
- **Biblioteca en tres capas**, buscador transversal, glosario contextual al pasar el ratón, botón «Explícamelo más simple» con dos niveles, y asistente de preguntas anclado en las fichas.

### `conocimiento.json`

Sin él la IA responde de conocimiento general y **puede inventar números de artículo**. El prompt del sistema le prohíbe citar lo que no puede sostener, pero la única garantía real es darle los textos:

```json
{
  "fuente": "Compilación normativa verificada, marzo 2026",
  "chunks": [
    { "id": "ley5307-art56", "tema": "Ley 53-07 conservación de datos", "texto": "…" }
  ]
}
```

Búsqueda por palabras, sin embeddings: no hace falta backend ni proceso de indexado.

## Lo que esta versión no hace, y por qué

Cuatro exigencias de la especificación **requieren servidor** y aquí no están. Están declaradas en la propia interfaz, no escondidas:

1. **Constancia verificable públicamente.** El código que emite se calcula en el navegador; cualquiera puede fabricar uno. La app lo dice en la constancia.
2. **Verificación de identidad al certificar.** No hay cuenta contra la que verificar.
3. **Sesión única y bloqueo de intentos simultáneos.** No hay sesión que bloquear.
4. **Registro de anomalías.** No hay dónde registrarlas.

Lo que sí se conserva del capítulo 6 son los controles de diseño de la prueba, que son los que la especificación considera más eficaces: banco infinito por generación, ítems de aplicación en vez de memoria, y aleatorización total.

Además, **la gratuidad no es completa**: la plataforma no cobra, pero el usuario paga a OpenAI. Un recorrido entero cuesta céntimos con `gpt-4o-mini`.

Y una advertencia que la app repite en cada ficha: **ningún contenido normativo está verificado en fuente oficial**. La especificación exige que toda afirmación tenga fuente y que cada ficha muestre su fecha de verificación. Mientras el comité editorial no verifique la biblioteca, la app declara el estado en vez de fingirlo.

## Estado

Fase 1 de la especificación, con las siete rutas presentes en lugar de dos. Pendiente: casos adicionales (difusión no consentida de imágenes íntimas, ataque a infraestructura pública, ingeniería social a empresa), examen de ruta con umbral del 80 %, examen integrador transversal y consulta sin conexión.

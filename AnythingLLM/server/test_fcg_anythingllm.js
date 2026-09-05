const path = require("path");
const assert = require("assert");

process.env.NODE_ENV = "development";

const ImportedPlugin = require("./utils/agents/imported");

console.log("==================================================================");
console.log("🔍 TEST: DETECCIÓN DE 'fcg-ppt' EN ANYTHINGLLM");
console.log("==================================================================");

async function testFCGSkill() {
  const hubId = "fcg-ppt";

  // 1. Validar Handler
  console.log("\n[1] Verificando handler de 'fcg-ppt'...");
  const isValidHandler = ImportedPlugin.validateImportedPluginHandler(hubId);
  console.log("-> Handler válido:", isValidHandler);
  assert.strictEqual(isValidHandler, true, "El handler debe ser detectado como válido por AnythingLLM.");

  // 2. Listar en UI
  console.log("\n[2] Verificando listado en ImportedPlugin.listImportedPlugins()...");
  const importedList = ImportedPlugin.listImportedPlugins();
  console.log(`-> Total de skills detectadas: ${importedList.length} (${importedList.map(s => s.hubId).join(", ")})`);
  const skillConfig = importedList.find(s => s.hubId === hubId);
  assert(skillConfig, "La skill 'fcg-ppt' DEBE aparecer listada en listImportedPlugins.");
  console.log("-> Nombre:", skillConfig.name);
  console.log("-> Activa:", skillConfig.active);
  console.log("-> Parámetros de entrypoint:", Object.keys(skillConfig.entrypoint.params));

  // 3. Verificar en plugins activos
  console.log("\n[3] Verificando inclusión en ImportedPlugin.activeImportedPlugins()...");
  const activePlugins = ImportedPlugin.activeImportedPlugins();
  console.log("-> Plugins activos:", activePlugins);
  assert(activePlugins.includes(`@@${hubId}`), `El array de plugins activos debe contener '@@${hubId}'`);

  // 4. Cargar y ejecutar handler simulado con aibitat
  console.log("\n[4] Probando invocación del handler a través de aibitat...");
  const pluginInstance = ImportedPlugin.loadPluginByHubId(hubId);
  const callOpts = pluginInstance.parseCallOptions();

  let registeredFnConfig = null;
  const mockAibitat = {
    function(fnConfig) { registeredFnConfig = fnConfig; return this; },
    introspect: (msg) => console.log(`   [UI Introspect] ${msg}`),
    handlerProps: { log: (msg, d) => console.log(`   [Logger] ${msg}`, d || "") },
    requestToolApproval: async ({ description }) => {
      console.log(`   [UI Approval Card] ${description}`);
      return { approved: true, message: "Aprobado por el usuario" };
    }
  };

  pluginInstance.plugin(callOpts).setup(mockAibitat);
  assert(registeredFnConfig, "La función no se registró correctamente.");

  console.log("\n   --> Invocando handler con parámetros de prueba...");
  const resultStr = await registeredFnConfig.handler.call(
    registeredFnConfig,
    {
      title: "Auditoría de Sistemas 2026",
      subtitle: "Evaluación Forense y Gobernanza",
      category: "AUDITORÍA",
      client: "Comité de Riesgos",
      action: "generate_deck"
    }
  );

  console.log("   -> Resultado JSON recibido:", resultStr);
  const result = JSON.parse(resultStr);
  assert.strictEqual(result.status, "success", "El status debe ser 'success'.");
  assert.strictEqual(result.slides_count, 6, "El número de diapositivas debe ser 6.");
  console.log(`\n✅ ARCHIVO GENERADO CON ÉXITO: ${result.filepath}`);
  console.log("==================================================================");
  console.log("🎉 'fcg-ppt' ESTÁ 100% RECONOCIDO Y OPERATIVO EN ANYTHINGLLM");
  console.log("==================================================================");
}

testFCGSkill().catch(err => {
  console.error("❌ ERROR EN LA VALIDACIÓN:", err);
  process.exit(1);
});

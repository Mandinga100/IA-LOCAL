const path = require("path");
const fs = require("fs");
const assert = require("assert");

// Force development environment so ImportedPlugin looks in server/storage/plugins/agent-skills
process.env.NODE_ENV = "development";

const ImportedPlugin = require("./utils/agents/imported");

console.log("==================================================================");
console.log("🧪 INICIANDO SUITE DE VALIDACIÓN FORENSE DE CUSTOM SKILLS (SDP-U)");
console.log("==================================================================");

async function runTests() {
  const hubId = "forensic-audit-skill";

  // -------------------------------------------------------------
  // TEST 1: Verificación de estructura de archivos y manifest
  // -------------------------------------------------------------
  console.log("\n[TEST 1] Verificando existencia de plugin.json y handler.js...");
  const isValidHandler = ImportedPlugin.validateImportedPluginHandler(hubId);
  console.log("-> Handler válido según ImportedPlugin:", isValidHandler);
  assert.strictEqual(isValidHandler, true, "El handler debe ser detectado como válido por AnythingLLM.");

  // -------------------------------------------------------------
  // TEST 2: Detección y listado en la interfaz (listImportedPlugins)
  // -------------------------------------------------------------
  console.log("\n[TEST 2] Verificando detección en ImportedPlugin.listImportedPlugins()...");
  const importedList = ImportedPlugin.listImportedPlugins();
  console.log(`-> Skills encontradas (${importedList.length}):`, importedList.map(s => s.hubId));
  const skillConfig = importedList.find(s => s.hubId === hubId);
  assert(skillConfig, "La skill debe aparecer listada en listImportedPlugins.");
  assert.strictEqual(skillConfig.name, "Forensic Audit Skill");
  assert.strictEqual(skillConfig.active, true);
  console.log("-> Configuración de setup_args detectada:", Object.keys(skillConfig.setup_args));
  console.log("-> Parámetros de entrypoint detectados:", Object.keys(skillConfig.entrypoint.params));

  // -------------------------------------------------------------
  // TEST 3: Activación en el clúster de agentes (activeImportedPlugins)
  // -------------------------------------------------------------
  console.log("\n[TEST 3] Verificando que ImportedPlugin.activeImportedPlugins() incluye la skill...");
  const activePlugins = ImportedPlugin.activeImportedPlugins();
  console.log("-> Skills activas para el Agente:", activePlugins);
  assert(activePlugins.includes(`@@${hubId}`), `El array de plugins activos debe contener '@@${hubId}'`);

  // -------------------------------------------------------------
  // TEST 4: Carga e Instanciación del Plugin
  // -------------------------------------------------------------
  console.log("\n[TEST 4] Cargando plugin con ImportedPlugin.loadPluginByHubId()...");
  const pluginInstance = ImportedPlugin.loadPluginByHubId(hubId);
  assert(pluginInstance, "No se pudo cargar la instancia del plugin.");
  const callOpts = pluginInstance.parseCallOptions();
  console.log("-> Opciones de llamada parseadas (runtimeArgs):", callOpts);
  assert.strictEqual(callOpts.HASH_ALGO, "sha256");

  // -------------------------------------------------------------
  // TEST 5: Integración con aibitat y requestToolApproval interactivo
  // -------------------------------------------------------------
  console.log("\n[TEST 5] Validando canal de aprobación interactiva (requestToolApproval)...");
  
  let registeredFnConfig = null;
  const introspectLogs = [];
  const consoleLogs = [];

  // Mock de aibitat con canal de aprobación interactivo simulado
  let mockUserDecision = false; // Simular rechazo primero
  let lastApprovalRequest = null;

  const mockAibitat = {
    function(fnConfig) {
      registeredFnConfig = fnConfig;
      return this;
    },
    introspect: (msg) => {
      introspectLogs.push(msg);
      console.log(`   [UI Introspect] ${msg}`);
    },
    handlerProps: {
      log: (msg, data) => {
        consoleLogs.push({ msg, data });
        console.log(`   [Logger] ${msg}`, data ? JSON.stringify(data) : "");
      }
    },
    requestToolApproval: async ({ skillName, payload, description }) => {
      lastApprovalRequest = { skillName, payload, description };
      console.log(`   [UI Prompt Card] "${skillName}": ${description}`);
      return {
        approved: mockUserDecision,
        message: mockUserDecision ? "Aprobado por el usuario." : "Acción denegada por directiva de seguridad del usuario."
      };
    }
  };

  const aibitatPlugin = pluginInstance.plugin(callOpts);
  aibitatPlugin.setup(mockAibitat);
  assert(registeredFnConfig, "La función no se registró correctamente en aibitat.");

  // SUB-TEST 5.1: Ejecutar acción crítica cuando el usuario RECHAZA
  console.log("\n   --> Sub-test 5.1: Invocación con acción 'delete_quarantine' y rechazo del usuario...");
  mockUserDecision = false;
  const rejectResultStr = await registeredFnConfig.handler.call(
    registeredFnConfig,
    { target_content: "malware_payload.exe", action: "delete_quarantine" }
  );
  console.log("   -> Resultado retornado al agente (String):", rejectResultStr);
  const rejectResult = JSON.parse(rejectResultStr);
  assert.strictEqual(rejectResult.status, "rejected");
  assert.strictEqual(rejectResult.authorized, false);
  assert.strictEqual(lastApprovalRequest.skillName, "Forensic Audit Skill");

  // SUB-TEST 5.2: Ejecutar acción crítica cuando el usuario APRUEBA
  console.log("\n   --> Sub-test 5.2: Invocación con acción 'hash' y aprobación del usuario...");
  mockUserDecision = true;
  const approveResultStr = await registeredFnConfig.handler.call(
    registeredFnConfig,
    { target_content: "CONFIDENTIAL_FINANCIAL_REPORT_2026.pdf", action: "hash" }
  );
  console.log("   -> Resultado retornado al agente (String):", approveResultStr);
  const approveResult = JSON.parse(approveResultStr);
  assert.strictEqual(approveResult.status, "success");
  assert.strictEqual(approveResult.authorized, true);
  assert.strictEqual(approveResult.hash_algorithm, "sha256");
  assert(approveResult.hash_fingerprint, "Debe contener el fingerprint SHA-256 calculado.");
  console.log("   -> Fingerprint SHA-256 verificado:", approveResult.hash_fingerprint);

  // -------------------------------------------------------------
  // TEST 6: Validación de HOT-RELOADING en vivo
  // -------------------------------------------------------------
  console.log("\n[TEST 6] Probando HOT-RELOADING de handler.js sin reiniciar el servidor...");
  const handlerPath = path.resolve(__dirname, "storage/plugins/agent-skills", hubId, "handler.js");
  const originalHandlerCode = fs.readFileSync(handlerPath, "utf8");

  try {
    // Inyectamos una modificación en caliente en handler.js
    console.log("-> Modificando handler.js en disco (inyectando v1.0.1 con HOT_RELOAD_ACTIVE = true)...");
    const hotReloadCode = originalHandlerCode.replace(
      'version: this.config?.version || "1.0.0",',
      'version: "1.0.1-hot-reloaded", hot_reload_verified: true,'
    );
    fs.writeFileSync(handlerPath, hotReloadCode, "utf8");

    // Recargamos el plugin usando ImportedPlugin (como lo hace AnythingLLM en cada sesión)
    const reloadedPluginInstance = ImportedPlugin.loadPluginByHubId(hubId);
    let reloadedFnConfig = null;
    const mockAibitatReload = {
      function(fnConfig) { reloadedFnConfig = fnConfig; return this; },
      introspect: () => {},
      handlerProps: { log: () => {} },
      requestToolApproval: async () => ({ approved: true, message: "ok" })
    };
    reloadedPluginInstance.plugin(callOpts).setup(mockAibitatReload);

    // Invocamos el handler recargado
    const reloadResultStr = await reloadedFnConfig.handler.call(
      reloadedFnConfig,
      { target_content: "audit_test.log", action: "inspect" }
    );
    const reloadResult = JSON.parse(reloadResultStr);
    console.log("-> Resultado tras hot-reload:", reloadResult);

    assert.strictEqual(
      reloadResult.version,
      "1.0.1-hot-reloaded",
      "El código nuevo en handler.js debió cargarse de inmediato sin reiniciar."
    );
    assert.strictEqual(
      reloadResult.hot_reload_verified,
      true,
      "La nueva propiedad inyectada debe estar presente."
    );
    console.log("✅ HOT-RELOADING CONFIRMADO AL 100%: require.cache se invalidó correctamente.");
  } finally {
    // Restaurar el código original
    fs.writeFileSync(handlerPath, originalHandlerCode, "utf8");
    console.log("-> Código original de handler.js restaurado.");
  }

  console.log("\n==================================================================");
  console.log("🎉 TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO: 100% OPERATIVO Y VALIDADO");
  console.log("==================================================================");
}

runTests().catch(err => {
  console.error("\n❌ ERROR EN LA SUITE DE PRUEBAS:", err);
  process.exit(1);
});

#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — envoltorio de hook para bridge-session.init.
 * La lógica vive en bridge-session.js; esto sólo cumple el contrato run().
 */

'use strict';

const { init } = require('./bridge-session');

module.exports = { run: rawInput => init(rawInput) };

#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — envoltorio de hook para bridge-session.close.
 * La lógica vive en bridge-session.js; esto sólo cumple el contrato run().
 */

'use strict';

const { close } = require('./bridge-session');

module.exports = { run: rawInput => close(rawInput) };

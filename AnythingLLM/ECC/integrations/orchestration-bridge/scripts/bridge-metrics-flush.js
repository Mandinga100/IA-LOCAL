#!/usr/bin/env node
/**
 * ECC Orchestration Bridge — envoltorio de hook para bridge-session.flush.
 * La lógica vive en bridge-session.js; esto sólo cumple el contrato run().
 */

'use strict';

const { flush } = require('./bridge-session');

module.exports = { run: rawInput => flush(rawInput) };

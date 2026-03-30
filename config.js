// This file loads environment variables from .env for local development
require('dotenv').config();

module.exports = {
  apiKey: process.env.GROQ_API_KEY,
};

// Optional syllabus demonstration: Node.js + Mongoose CRUD API.
// Run from node_integration/: npm install, copy .env.example to .env, npm start
require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const app = express();
app.use(express.json());
const cropSchema = new mongoose.Schema({
  Crop: { type: String, required: true, trim: true },
  Crop_Year: { type: Number, required: true, min: 1900 },
  Season: { type: String, required: true, trim: true },
  State: { type: String, required: true, trim: true },
  Area: { type: Number, required: true, min: 0 },
  Production: { type: Number, required: true, min: 0 },
  Annual_Rainfall: { type: Number, required: true, min: 0 },
  Fertilizer: { type: Number, required: true, min: 0 },
  Pesticide: { type: Number, required: true, min: 0 },
  Yield: { type: Number, required: true, min: 0 }
}, { collection: 'crops', strict: true });
cropSchema.index({ State: 1, Crop_Year: -1 });
cropSchema.index({ Crop: 1, Season: 1 });
const Crop = mongoose.model('Crop', cropSchema);
app.get('/health', (_req, res) => res.json({status: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected'}));
app.get('/api/crops', async (req, res) => {
  try { const page = Math.max(1, Number(req.query.page) || 1); const limit = Math.min(100, Math.max(1, Number(req.query.limit) || 20)); const docs = await Crop.find().sort({Crop_Year:-1}).skip((page-1)*limit).limit(limit).lean(); res.json({page, limit, data:docs}); }
  catch (e) { res.status(500).json({error:'Unable to list crops'}); }
});
app.post('/api/crops', async (req, res) => {
  try { const doc = await Crop.create(req.body); res.status(201).json(doc); }
  catch (e) { res.status(400).json({error:e.message}); }
});
app.patch('/api/crops/:id', async (req, res) => {
  try { const doc = await Crop.findByIdAndUpdate(req.params.id, req.body, {new:true, runValidators:true}); if (!doc) return res.status(404).json({error:'Not found'}); res.json(doc); }
  catch (e) { res.status(400).json({error:e.message}); }
});
app.delete('/api/crops/:id', async (req, res) => {
  try { const doc = await Crop.findByIdAndDelete(req.params.id); if (!doc) return res.status(404).json({error:'Not found'}); res.status(204).end(); }
  catch (e) { res.status(400).json({error:e.message}); }
});
const port = process.env.PORT || 3000;
mongoose.connect(process.env.MONGO_URI || 'mongodb://localhost:27017/agriyield_db')
  .then(() => app.listen(port, () => console.log(`Mongoose demo listening on http://localhost:${port}`)))
  .catch(err => { console.error('MongoDB connection failed:', err.message); process.exit(1); });

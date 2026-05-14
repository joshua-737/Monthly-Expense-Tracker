/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useMemo } from 'react';
import { 
  Building2, 
  Coins, 
  TrendingUp, 
  Wallet, 
  Plus, 
  Trash2, 
  Edit2, 
  ChevronRight, 
  AlertCircle, 
  CheckCircle2,
  Calendar,
  Layers,
  History,
  Activity,
  User,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  Legend
} from 'recharts';
import { format, parseISO, startOfMonth, isSameMonth, isSameYear, subMonths } from 'date-fns';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import axios from 'axios';

// Helper for tailwind classes
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Types ---
enum Category {
  NEEDS = "NEEDS",
  WANTS = "WANTS",
  INVESTMENTS = "INVESTMENTS",
  MISC = "MISC"
}

interface Expense {
  id: string;
  amount: number;
  description: string;
  category: Category;
  timestamp: string;
}

interface AppData {
  expenses: Expense[];
  capital: number;
}

// --- Constants & Keywords ---
const COLORS = {
  [Category.NEEDS]: "#64748B",
  [Category.WANTS]: "#A78BBA",
  [Category.MISC]: "#BEBEC4",
  [Category.INVESTMENTS]: "#D4A574"
};

const CATEGORY_KEYWORDS = {
  [Category.NEEDS]: [
    'food', 'pani puri', 'biryani', 'chai', 'tea', 'coffee', 'meals', 'breakfast', 'lunch', 'dinner', 'snacks', 'groceries', 'vegetables', 'fruits', 'rice', 'dal', 'bread', 'eggs', 'milk', 'butter', 'oil', 'spices',
    'bus', 'auto', 'rickshaw', 'cab', 'ola', 'uber', 'train', 'metro', 'commute', 'transport', 'petrol', 'diesel', 'fuel', 'bike', 'car', 'vehicle', 'parking',
    'rent', 'house', 'apartment', 'accommodation', 'bills', 'electricity', 'water', 'gas', 'cylinder', 'internet', 'mobile', 'phone', 'recharge', 'landline',
    'medicine', 'hospital', 'doctor', 'pharmacy', 'chemist', 'health', 'medical', 'dental', 'clinic', 'healthcare',
    'school', 'college', 'tuition', 'fees', 'education', 'books', 'stationery', 'notebook', 'pen', 'study', 'exam',
    'maintenance', 'repair', 'plumbing', 'electrical', 'carpentry', 'cleaning'
  ],
  [Category.WANTS]: [
    'projector', 'gaming', 'console', 'controller', 'steam', 'game', 'ps5', 'xbox', 'nintendo',
    'netflix', 'amazon prime', 'hotstar', 'spotify', 'disney+', 'subscription', 'streaming', 'music',
    'clothes', 'shoes', 'sneakers', 'shirt', 'pants', 'dress', 'jeans', 'fashion', 'apparel', 'accessories',
    'party', 'club', 'hangout', 'outing', 'entertainment', 'movie', 'cinema', 'theatre', 'shows', 'concert',
    'luxury', 'premium', 'expensive', 'high-end', 'branded', 'designer',
    'zomato', 'swiggy', 'blinkit', 'zepto', 'restaurant', 'cafe', 'coffee shop', 'ice cream', 'dessert', 'chocolate', 'chips', 'junk food', 'fast food', 'mcdonalds', 'kfc', 'burger', 'pizza', 'delivery',
    'gadget', 'headphones', 'earphones', 'airpods', 'keyboard', 'mouse', 'monitor', 'phone', 'laptop', 'tablet', 'electronics', 'device',
    'watch', 'ring', 'jewelry', 'necklace', 'bracelet', 'accessories',
    'gift', 'toy', 'decoration', 'hobby', 'art', 'craft', 'DIY',
    'alcohol', 'cigarette', 'tobacco', 'vape', 'smoking',
    'salon', 'spa', 'haircut', 'skincare', 'makeup', 'perfume', 'grooming', 'cosmetics', 'beauty',
    'travel', 'trip', 'vacation', 'hotel', 'resort', 'flight', 'booking', 'tourism', 'getaway',
    'sports', 'gym', 'yoga', 'fitness', 'equipment', 'gear', 'training', 'workshop', 'class'
  ],
  [Category.INVESTMENTS]: [
    'invest', 'stocks', 'mutual fund', 'sip', 'gold', 'crypto', 'bitcoin', 'ethereum', 'nft', 'fd', 'fixed deposit', 'savings', 'deposit', 'nps', 'ppf', 'insurance', 'pension', 'retirement', 'provident fund', 'bond'
  ]
};

// --- Logic ---
const categorizeInput = (text: string): Category => {
  const lowerText = text.toLowerCase();
  
  // Create a priority logic: Investments > Needs > Wants
  // We check for exact substring matches
  for (const keyword of CATEGORY_KEYWORDS[Category.INVESTMENTS]) {
    if (lowerText.includes(keyword)) return Category.INVESTMENTS;
  }
  for (const keyword of CATEGORY_KEYWORDS[Category.NEEDS]) {
    if (lowerText.includes(keyword)) return Category.NEEDS;
  }
  for (const keyword of CATEGORY_KEYWORDS[Category.WANTS]) {
    if (lowerText.includes(keyword)) return Category.WANTS;
  }
  
  return Category.MISC;
};

const parseExpenseInput = (input: string) => {
  const amountMatch = input.match(/(\d+(\.\d+)?)/);
  if (!amountMatch) return null;
  
  const amount = parseFloat(amountMatch[1]);
  // Remove the "for" if it exists after the number, or just the number itself
  let description = input.replace(amountMatch[0], "").trim();
  if (description.toLowerCase().startsWith("for ")) {
    description = description.substring(4).trim();
  }
  
  if (!description) description = "Unspecified expense";
  
  const category = categorizeInput(description);
  
  return { amount, description, category };
};

// --- Components ---

export default function App() {
  const [data, setData] = useState<AppData>({ expenses: [], capital: 0 });
  const [inputText, setInputText] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [view, setView] = useState<'lifetime' | 'month'>('lifetime');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Partial<Expense>>({});

  // Initialize data
  useEffect(() => {
    axios.get('/api/expenses')
      .then(res => {
        if (res.data && res.data.expenses) {
          setData(res.data);
        }
      })
      .catch(err => console.error("Could not fetch data:", err));
  }, []);

  // Save data whenever it changes
  const saveData = async (newData: AppData) => {
    setData(newData);
    try {
      await axios.post('/api/save', newData);
    } catch (err) {
      console.error("Failed to save data:", err);
    }
  };

  const handleAddExpense = (e: React.FormEvent) => {
    e.preventDefault();
    const result = parseExpenseInput(inputText);
    if (!result) return;

    const newExpense: Expense = {
      id: crypto.randomUUID(),
      amount: result.amount,
      description: result.description,
      category: result.category,
      timestamp: new Date().toISOString()
    };

    const newData = {
      ...data,
      expenses: [newExpense, ...data.expenses]
    };
    saveData(newData);
    setInputText("");
  };

  const handleDeleteExpense = (id: string) => {
    if (!window.confirm("Are you sure you want to delete this expense?")) return;
    const newData = {
      ...data,
      expenses: data.expenses.filter(e => e.id !== id)
    };
    saveData(newData);
  };

  const handleEditExpense = (id: string) => {
    const expense = data.expenses.find(e => e.id === id);
    if (expense) {
      setEditingId(id);
      setEditValues(expense);
    }
  };

  const saveEdit = () => {
    if (!editingId) return;
    const newData = {
      ...data,
      expenses: data.expenses.map(e => e.id === editingId ? { ...e, ...editValues } as Expense : e)
    };
    saveData(newData);
    setEditingId(null);
  };

  const handleUpdateCapital = (val: number) => {
    saveData({ ...data, capital: val });
  };

  // Metrics
  const totalCapital = data.capital;
  const untouchableSeed = totalCapital * 0.1;
  const wealthBuilt = data.expenses
    .filter(e => e.category === Category.INVESTMENTS)
    .reduce((acc, curr) => acc + curr.amount, 0);
  
  const totalAllExpenses = data.expenses
    .reduce((acc, curr) => acc + curr.amount, 0);
    
  const spendableBalance = totalCapital - untouchableSeed - totalAllExpenses;

  // Suggestions Logic
  const suggestions = useMemo(() => {
    if (!inputText || inputText.length < 2) return [];
    
    // Extract description part if user already started typing amounts
    const parts = inputText.split(/\s+/);
    const lastWord = parts[parts.length - 1].toLowerCase();
    
    // Unique past descriptions
    const uniqueDescs: string[] = Array.from(new Set(data.expenses.map(e => e.description)));
    
    return uniqueDescs
      .filter((d: string) => d.toLowerCase().includes(lastWord) && d.toLowerCase() !== lastWord)
      .slice(0, 5);
  }, [inputText, data.expenses]);

  const handleApplySuggestion = (suggestion: string) => {
    // If input has a number, keep the number and replace the description
    const amountMatch = inputText.match(/(\d+(\.\d+)?)/);
    if (amountMatch) {
      setInputText(`${amountMatch[0]} for ${suggestion}`);
    } else {
      setInputText(suggestion);
    }
    setShowSuggestions(false);
  };

  // Monthly Filter
  const now = new Date();
  const filteredExpenses = useMemo(() => {
    if (view === 'lifetime') return data.expenses;
    return data.expenses.filter(e => {
      const d = parseISO(e.timestamp);
      return isSameMonth(d, now) && isSameYear(d, now);
    });
  }, [data.expenses, view]);

  // Chart Data: Monthly Spending
  const getMonthlyChartData = () => {
    const months: Record<string, any> = {};
    const last6 = Array.from({ length: 6 }).map((_, i) => subMonths(now, i)).reverse();
    
    last6.forEach(m => {
      const key = format(m, 'MMM yyyy');
      months[key] = { name: key, [Category.NEEDS]: 0, [Category.WANTS]: 0, [Category.MISC]: 0 };
    });

    data.expenses.forEach(e => {
      if (e.category === Category.INVESTMENTS) return;
      const key = format(parseISO(e.timestamp), 'MMM yyyy');
      if (months[key]) {
        months[key][e.category] += e.amount;
      }
    });

    return Object.values(months);
  };

  const getPieData = () => {
    const sums = {
      [Category.NEEDS]: 0,
      [Category.WANTS]: 0,
      [Category.MISC]: 0,
      [Category.INVESTMENTS]: 0
    };
    
    data.expenses.forEach(e => {
      sums[e.category] += e.amount;
    });

    return [
      { name: 'Needs', value: sums[Category.NEEDS], color: COLORS[Category.NEEDS] },
      { name: 'Wants', value: sums[Category.WANTS], color: COLORS[Category.WANTS] },
      { name: 'Misc', value: sums[Category.MISC], color: COLORS[Category.MISC] },
      { name: 'Investments', value: sums[Category.INVESTMENTS], color: COLORS[Category.INVESTMENTS] },
    ].filter(v => v.value > 0);
  };

  // Oracle Wisdom
  const currentMonthTotals = useMemo(() => {
    const current = data.expenses.filter(e => isSameMonth(parseISO(e.timestamp), now));
    const needs = current.filter(e => e.category === Category.NEEDS).reduce((a, b) => a + b.amount, 0);
    const wants = current.filter(e => e.category === Category.WANTS).reduce((a, b) => a + b.amount, 0);
    const misc = current.filter(e => e.category === Category.MISC).reduce((a, b) => a + b.amount, 0);
    const investments = current.filter(e => e.category === Category.INVESTMENTS).reduce((a, b) => a + b.amount, 0);
    return { needs, wants, misc, investments };
  }, [data.expenses]);

  const lifetimeTotals = useMemo(() => {
    const needs = data.expenses.filter(e => e.category === Category.NEEDS).reduce((a, b) => a + b.amount, 0);
    const wants = data.expenses.filter(e => e.category === Category.WANTS).reduce((a, b) => a + b.amount, 0);
    const misc = data.expenses.filter(e => e.category === Category.MISC).reduce((a, b) => a + b.amount, 0);
    const investments = data.expenses.filter(e => e.category === Category.INVESTMENTS).reduce((a, b) => a + b.amount, 0);
    return { needs, wants, misc, investments };
  }, [data.expenses]);

  return (
    <div className="min-h-screen bg-[#FFFFFF] text-[#1F2937] font-sans selection:bg-[#B8956A]/20">
      {/* Header / Capital Update */}
      <header className="max-w-7xl mx-auto px-6 py-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-4xl font-light tracking-tight flex items-center gap-3">
            <Building2 className="w-10 h-10 text-[#B8956A]" />
            The Babylon Vault
          </h1>
          <p className="text-[#9CA3AF] mt-1 font-medium italic">Seek thee gold, but guard the gates.</p>
        </div>
        
        <div className="flex flex-col gap-2">
          <label className="text-xs uppercase tracking-widest text-[#9CA3AF] font-bold">Update My Capital (₹)</label>
          <div className="relative group">
            <input 
              type="number" 
              value={data.capital || ""} 
              onChange={(e) => handleUpdateCapital(parseFloat(e.target.value) || 0)}
              className="bg-[#F3F4F6] border-none rounded-xl px-5 py-3 w-64 focus:ring-2 focus:ring-[#B8956A]/50 outline-none transition-all font-mono text-lg font-semibold"
              placeholder="0.00"
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#9CA3AF]">₹</div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 space-y-12 pb-24">
        
        {/* SECTION 1 — THE VAULT */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-[#F3F4F6] p-8 rounded-2xl flex flex-col justify-between min-h-[140px] group transition-all hover:bg-[#F3F4F6]/80">
            <span className="text-sm font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Total Capital</span>
            <div className="text-4xl font-black tabular-nums tracking-tight">₹{totalCapital.toLocaleString()}</div>
          </div>
          
          <div className="bg-[#F3F4F6] p-8 rounded-2xl flex flex-col justify-between min-h-[140px] border-l-4 border-[#B8956A]">
            <span className="text-sm font-bold text-[#B8956A] uppercase tracking-wider mb-2">Gold for the Future</span>
            <div className="flex flex-col">
              <span className="text-4xl font-black tabular-nums text-[#B8956A]">₹{untouchableSeed.toLocaleString()}</span>
              <span className="text-[10px] font-bold text-[#9CA3AF] uppercase mt-1">Untouchable Seed</span>
            </div>
          </div>

          <div className="bg-[#F3F4F6] p-8 rounded-2xl flex flex-col justify-between min-h-[140px]">
            <span className="text-sm font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Spendable Balance</span>
            <div className="text-4xl font-black tabular-nums tracking-tight">₹{spendableBalance.toLocaleString()}</div>
          </div>

          <div className="bg-[#F3F4F6] p-8 rounded-2xl flex flex-col justify-between min-h-[140px]">
            <span className="text-sm font-bold text-[#9CA3AF] uppercase tracking-wider mb-2">Wealth Built</span>
            <div className="flex flex-col">
              <span className="text-4xl font-black tabular-nums text-[#D4A574]">₹{wealthBuilt.toLocaleString()}</span>
              <span className="text-[10px] font-bold text-[#9CA3AF] uppercase mt-1">Total Investments</span>
            </div>
          </div>
        </section>

        {/* SECTION 2 — THE AUDITOR (Expense Input) */}
        <section className="max-w-2xl mx-auto w-full relative">
          <form onSubmit={handleAddExpense} className="relative z-20">
            <input 
              type="text"
              value={inputText}
              onChange={(e) => {
                setInputText(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              placeholder="e.g. 40 for pani puri or 5000 for SIP"
              className="w-full bg-[#F3F4F6] border-none rounded-2xl px-8 py-6 text-xl focus:ring-2 focus:ring-[#B8956A]/30 outline-none transition-all pr-24 font-medium"
            />
            <button 
              type="submit"
              className="absolute right-4 top-1/2 -translate-y-1/2 bg-[#1F2937] text-white p-3 rounded-xl hover:bg-black transition-colors"
            >
              <ArrowRight className="w-6 h-6" />
            </button>
          </form>

          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-[#F3F4F6] overflow-hidden z-30 animate-in fade-in slide-in-from-top-2">
              <div className="p-2 border-b border-[#F3F4F6] text-[10px] font-black uppercase tracking-widest text-[#9CA3AF] px-4 py-3 flex justify-between items-center">
                <span>Past Wisdom</span>
                <button onClick={() => setShowSuggestions(false)} className="hover:text-[#1F2937]">Close</button>
              </div>
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplySuggestion(s)}
                  className="w-full text-left px-6 py-4 hover:bg-[#F3F4F6] transition-colors flex items-center gap-3 group"
                >
                  <History className="w-4 h-4 text-[#9CA3AF] group-hover:text-[#B8956A]" />
                  <span className="font-semibold">{s}</span>
                </button>
              ))}
            </div>
          )}

          <div className="mt-4 flex justify-center gap-6 text-[10px] font-bold text-[#9CA3AF] uppercase tracking-widest">
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[Category.NEEDS]}} /> Needs</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[Category.WANTS]}} /> Wants</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[Category.INVESTMENTS]}} /> Investments</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[Category.MISC]}} /> Misc</span>
          </div>
        </section>

        {/* SECTION 3 & 4 — EXPENSE MANAGEMENT */}
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex bg-[#F3F4F6] p-1.5 rounded-2xl">
              <button 
                onClick={() => setView('lifetime')}
                className={cn(
                  "px-6 py-2 rounded-xl text-sm font-bold transition-all",
                  view === 'lifetime' ? "bg-white shadow-sm text-[#1F2937]" : "text-[#9CA3AF] hover:text-[#1F2937]"
                )}
              >
                Lifetime View
              </button>
              <button 
                onClick={() => setView('month')}
                className={cn(
                  "px-6 py-2 rounded-xl text-sm font-bold transition-all",
                  view === 'month' ? "bg-white shadow-sm text-[#1F2937]" : "text-[#9CA3AF] hover:text-[#1F2937]"
                )}
              >
                Current Month View
              </button>
            </div>
            
            <button 
              onClick={() => {
                if (window.confirm("ARE YOU SURE? This will clear all thy records!")) {
                  saveData({...data, expenses: []});
                }
              }}
              className="px-6 py-2 text-xs font-bold uppercase tracking-widest text-red-500 hover:text-red-600 transition-colors"
            >
              Clear All Records
            </button>
          </div>

          <div className="overflow-x-auto rounded-3xl border border-[#F3F4F6]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#F3F4F6] text-[10px] uppercase tracking-widest font-black text-[#9CA3AF]">
                  <th className="px-8 py-5">Date / Time</th>
                  <th className="px-8 py-5">Description</th>
                  <th className="px-8 py-5">Category</th>
                  <th className="px-8 py-5 text-right">Amount (₹)</th>
                  <th className="px-8 py-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3F4F6]">
                {filteredExpenses.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-8 py-24 text-center text-[#9CA3AF] font-medium italic">
                      The ledger is empty. Start thy journey toward wealth.
                    </td>
                  </tr>
                ) : (
                  <>
                    {filteredExpenses.map((e) => (
                      <tr key={e.id} className="group hover:bg-[#F3F4F6]/30 transition-colors">
                        <td className="px-8 py-5 text-sm tabular-nums text-[#9CA3AF]">
                          {format(parseISO(e.timestamp), "dd-MM-yyyy HH:mm")}
                        </td>
                        <td className="px-8 py-5">
                          {editingId === e.id ? (
                            <input 
                              value={editValues.description} 
                              onChange={v => setEditValues({...editValues, description: v.target.value})}
                              className="bg-white border-2 border-[#B8956A]/20 px-3 py-1 rounded-lg outline-none focus:border-[#B8956A]"
                            />
                          ) : (
                            <span className="font-semibold">{e.description}</span>
                          )}
                        </td>
                        <td className="px-8 py-5">
                          {editingId === e.id ? (
                            <select 
                              value={editValues.category} 
                              onChange={v => setEditValues({...editValues, category: v.target.value as Category})}
                              className="bg-white border-2 border-[#B8956A]/20 px-3 py-1 rounded-lg outline-none"
                            >
                              <option value={Category.NEEDS}>Needs</option>
                              <option value={Category.WANTS}>Wants</option>
                              <option value={Category.INVESTMENTS}>Investments</option>
                              <option value={Category.MISC}>Misc</option>
                            </select>
                          ) : (
                            <span 
                              className="text-[10px] font-black uppercase tracking-widest px-3 py-1 rounded-full"
                              style={{ backgroundColor: `${COLORS[e.category] || '#CCC'}20`, color: COLORS[e.category] }}
                            >
                              {e.category}
                            </span>
                          )}
                        </td>
                        <td className="px-8 py-5 text-right tabular-nums font-mono font-bold">
                          {editingId === e.id ? (
                            <input 
                              type="number"
                              value={editValues.amount} 
                              onChange={v => setEditValues({...editValues, amount: parseFloat(v.target.value) || 0})}
                              className="bg-white border-2 border-[#B8956A]/20 px-3 py-1 rounded-lg outline-none w-24 text-right"
                            />
                          ) : (
                            `₹${e.amount.toLocaleString()}`
                          )}
                        </td>
                        <td className="px-8 py-5 text-right">
                          <div className="flex justify-end gap-2">
                            {editingId === e.id ? (
                              <button 
                                onClick={saveEdit}
                                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                              >
                                <CheckCircle2 className="w-5 h-5" />
                              </button>
                            ) : (
                              <button 
                                onClick={() => handleEditExpense(e.id)}
                                className="p-2 text-[#9CA3AF] hover:text-[#1F2937] hover:bg-[#F3F4F6] rounded-lg transition-all"
                              >
                                <Edit2 className="w-5 h-5" />
                              </button>
                            )}
                            <button 
                              onClick={() => handleDeleteExpense(e.id)}
                              className="p-2 text-[#9CA3AF] hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                            >
                              <Trash2 className="w-5 h-5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-[#F3F4F6]/50 font-black">
                      <td colSpan={3} className="px-8 py-6 text-right uppercase tracking-[0.2em] text-[10px] text-[#9CA3AF]">
                        Total Used This View
                      </td>
                      <td className="px-8 py-6 text-right tabular-nums font-mono text-lg text-[#1F2937]">
                        ₹{filteredExpenses.reduce((sum, e) => sum + e.amount, 0).toLocaleString()}
                      </td>
                      <td></td>
                    </tr>
                    {view === 'month' && (
                      <tr className="bg-[#B8956A]/5 font-black border-t border-[#B8956A]/10">
                        <td colSpan={3} className="px-8 py-4 text-right uppercase tracking-[0.2em] text-[10px] text-[#B8956A]">
                          Lifetime Total Used
                        </td>
                        <td className="px-8 py-4 text-right tabular-nums font-mono text-[#B8956A]">
                          ₹{data.expenses.reduce((sum, e) => sum + e.amount, 0).toLocaleString()}
                        </td>
                        <td></td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* SECTION 5 — ANALYTICS */}
        <section className="space-y-8">
          <h2 className="text-2xl font-light tracking-tight flex items-center gap-3">
            <Activity className="w-7 h-7 text-[#B8956A]" />
            The Oracle — Monthly Insights
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-[#F3F4F6]/50 p-8 rounded-3xl min-h-[400px]">
              <h3 className="text-sm font-bold uppercase tracking-widest text-[#9CA3AF] mb-8">Spending History (6 Months)</h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getMonthlyChartData()} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#9CA3AF' }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 700, fill: '#9CA3AF' }} />
                    <Tooltip 
                      cursor={{ fill: 'transparent' }}
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontWeight: 700 }}
                    />
                    <Bar dataKey={Category.NEEDS} fill={COLORS[Category.NEEDS]} radius={[4, 4, 0, 0]} />
                    <Bar dataKey={Category.WANTS} fill={COLORS[Category.WANTS]} radius={[4, 4, 0, 0]} />
                    <Bar dataKey={Category.MISC} fill={COLORS[Category.MISC]} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-[#F3F4F6]/50 p-8 rounded-3xl min-h-[400px] flex flex-col justify-center items-center">
              <h3 className="text-sm font-bold uppercase tracking-widest text-[#9CA3AF] mb-8 w-full">Lifetime Breakdown</h3>
              <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={getPieData()}
                      cx="50%"
                      cy="50%"
                      innerRadius={80}
                      outerRadius={110}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {getPieData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)', fontWeight: 700 }}
                    />
                    <Legend iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION 6 — WEALTH REPORT */}
        <section className="bg-[#F3F4F6] p-10 rounded-[2rem] space-y-10">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div>
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#9CA3AF] mb-4">Current Month</h4>
              <ul className="space-y-3 font-semibold tabular-nums">
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Needs</span>
                  <span className="text-[#64748B]">₹{currentMonthTotals.needs.toLocaleString()}</span>
                </li>
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Wants</span>
                  <span className="text-[#A78BBA]">₹{currentMonthTotals.wants.toLocaleString()}</span>
                </li>
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Misc</span>
                  <span className="text-[#BEBEC4]">₹{currentMonthTotals.misc.toLocaleString()}</span>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#9CA3AF] mb-4">Lifetime</h4>
              <ul className="space-y-3 font-semibold tabular-nums">
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Needs</span>
                  <span className="text-[#64748B]">₹{lifetimeTotals.needs.toLocaleString()}</span>
                </li>
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Wants</span>
                  <span className="text-[#A78BBA]">₹{lifetimeTotals.wants.toLocaleString()}</span>
                </li>
                <li className="flex justify-between items-center bg-white/50 px-4 py-2 rounded-xl">
                  <span>Misc</span>
                  <span className="text-[#BEBEC4]">₹{lifetimeTotals.misc.toLocaleString()}</span>
                </li>
              </ul>
            </div>

            <div className="flex flex-col justify-center text-center p-6 bg-[#B8956A]/5 rounded-[1.5rem] border border-[#B8956A]/20">
              <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#B8956A] mb-2">Wealth Built Contribution</h4>
              <div className="text-4xl font-black text-[#B8956A] mb-1">₹{lifetimeTotals.investments.toLocaleString()}</div>
              <p className="text-[10px] font-medium italic text-[#9CA3AF]">The walls of Babylon grow stronger.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contextual Wisdom */}
            {currentMonthTotals.wants > (spendableBalance * 0.2) && (
               <div className="bg-[#FEF3C7] p-6 rounded-2xl flex gap-4 items-start border border-amber-200 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                  <AlertCircle className="w-6 h-6 text-amber-600 shrink-0" />
                  <p className="text-amber-900 font-medium leading-relaxed">
                    Thy purse is leaking! The rich man controls his expenditures. Thy "Wants" exceed 20% of thy spendable gold.
                  </p>
               </div>
            )}
            
            {currentMonthTotals.needs > (totalCapital * 0.7) && (
               <div className="bg-[#FEF3C7] p-6 rounded-2xl flex gap-4 items-start border border-amber-200 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                  <AlertCircle className="w-6 h-6 text-amber-600 shrink-0" />
                  <p className="text-amber-900 font-medium leading-relaxed">
                    Thou art surviving, not building. Needs consume more than 70% of thy capital. Seek ways to grow thy income.
                  </p>
               </div>
            )}

            {currentMonthTotals.wants < (spendableBalance * 0.2) && (currentMonthTotals.needs + currentMonthTotals.wants + currentMonthTotals.misc) > 0 && (
               <div className="bg-[#ECFDF5] p-6 rounded-2xl flex gap-4 items-start border border-emerald-200 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                  <p className="text-emerald-900 font-medium leading-relaxed">
                    Well done. A portion of all you earn is yours to keep. The walls of Babylon hold.
                  </p>
               </div>
            )}

            {lifetimeTotals.investments > 0 && (
               <div className="bg-[#ECFDF5] p-6 rounded-2xl flex gap-4 items-start border border-emerald-200 shadow-sm animate-in fade-in slide-in-from-bottom-2">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                  <p className="text-emerald-900 font-medium leading-relaxed">
                    A man who builds wealth first pays himself. Babylon smiles upon thee for thy investments.
                  </p>
               </div>
            )}
          </div>
        </section>

      </main>

      <footer className="text-center py-12 border-t border-[#F3F4F6] text-[10px] font-bold text-[#9CA3AF] uppercase tracking-[0.3em]">
        The Richest Man in Babylon • Built for Thee
      </footer>
    </div>
  );
}

const { useState, useEffect } = React;

const Icon = ({ name, className }) => {
    useEffect(() => {
        if (window.lucide) window.lucide.createIcons();
    }, [name]);
    return <i data-lucide={name} className={className}></i>;
};

const App = () => {
    const [activeTab, setActiveTab] = useState('free');
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const activities = [
        {
            id: 1,
            title: "The Free Bus System",
            category: "free",
            tag: "Transit Hack",
            description: "Avoid $30+ parking fees. Vail's internal bus system is 100% free and runs between the Village and Lionshead every few minutes.",
            highlights: ["Saves $30/day in parking", "Heated waiting areas", "Goes to grocery stores"],
            icon: "bus",
            image: "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=800"
        },
        {
            id: 2,
            title: "Booth Falls Hike",
            category: "free",
            tag: "Nature",
            description: "A stunning 4-mile round trip hike to a massive waterfall. Incredible views of the valley for exactly zero dollars.",
            highlights: ["Iconic photo spots", "Wildlife sightings", "Accessible via free bus"],
            icon: "mountain",
            image: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=800"
        },
        {
            id: 3,
            title: "Snowsports Museum",
            category: "free",
            tag: "Culture",
            description: "Located in the Village parking structure. Learn about the 10th Mountain Division. Entry is free (donations welcome).",
            highlights: ["Indoor activity", "Historic artifacts", "Great for dating"],
            icon: "award",
            image: "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&q=80&w=800"
        },
        {
            id: 4,
            title: "Village Picnic Spots",
            category: "free",
            tag: "Dating",
            description: "Skip the $100 lunches. Grab local groceries and eat by Gore Creek. Best romantic views without the bill.",
            highlights: ["River-side seating", "Quiet park areas", "Local's favorite"],
            icon: "heart",
            image: "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?auto=format&fit=crop&q=80&w=800"
        },
        {
            id: 5,
            title: "Nature Discovery Center",
            category: "free",
            tag: "Kids",
            description: "Located at Eagle's Nest. If you hike up Berry Picker trail, access to this education center is totally free.",
            highlights: ["Interactive wildlife exhibits", "Naturalist programs", "Conservation focus"],
            icon: "tree-pine",
            image: "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&q=80&w=800"
        },
        {
            id: 6,
            title: "Local Brewery Happy Hour",
            category: "low-cost",
            tag: "Social",
            description: "Vail Brewing Co (VBC) offers more affordable pints and a community vibe compared to hotel bars.",
            highlights: ["$7-9 Pints", "Dog friendly", "Food truck access"],
            icon: "beer",
            image: "https://images.unsplash.com/photo-1538333581680-72990666072b?auto=format&fit=crop&q=80&w=800"
        }
    ];

    const filteredActivities = activeTab === 'all'
        ? activities
        : activities.filter(a => a.category === activeTab);

    return (
        <div className="min-h-screen">
            <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'glass-nav shadow-md py-3' : 'bg-transparent py-6'}`}>
                <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Icon name="mountain" className={`w-8 h-8 ${scrolled ? 'text-blue-600' : 'text-white'}`} />
                        <span className={`text-xl font-black tracking-tighter ${scrolled ? 'text-slate-900' : 'text-white'}`}>VAIL LOCAL</span>
                    </div>
                    <div className="hidden md:flex gap-8 items-center font-bold text-sm">
                        <a href="#hacks" className={scrolled ? 'text-slate-600' : 'text-white'}>Budget Hacks</a>
                        <a href="#activities" className={scrolled ? 'text-slate-600' : 'text-white'}>Free Stuff</a>
                        <button className="bg-blue-600 text-white px-5 py-2 rounded-full shadow-lg">Plan Your Move</button>
                    </div>
                </div>
            </nav>

            <section className="relative h-[80vh] flex items-center justify-center text-center overflow-hidden">
                <div className="absolute inset-0 z-0">
                    <img src="https://images.unsplash.com/photo-1486496146582-9ffcd0b2b2b7?auto=format&fit=crop&q=80&w=2000" className="w-full h-full object-cover brightness-[0.45]" alt="Vail View" />
                    <div className="absolute inset-0 hero-gradient" />
                </div>
                <div className="relative z-10 max-w-4xl px-6">
                    <h1 className="text-5xl md:text-8xl font-black mb-4 text-white tracking-tight leading-none">
                        Vail for the <span className="text-emerald-400">Rest of Us</span>
                    </h1>
                    <p className="text-lg md:text-xl text-slate-200 max-w-2xl mx-auto mb-10 font-medium">
                        Skip the $20 hot cocoa. Discover how to hike, play, and explore Vail for free (or close to it).
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="#activities" className="bg-emerald-500 text-white px-8 py-4 rounded-2xl font-black hover:bg-emerald-600 transition-all flex items-center justify-center gap-2">
                            <Icon name="search" className="w-5 h-5" /> Find Free Activities
                        </a>
                    </div>
                </div>
            </section>

            <section id="hacks" className="relative z-20 -mt-20 max-w-6xl mx-auto px-6 mb-24">
                <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-8">
                    <div className="flex gap-4 items-start">
                        <div className="p-3 bg-blue-100 text-blue-600 rounded-2xl"><Icon name="bus" /></div>
                        <div>
                            <h4 className="font-black text-slate-900">Free Bus Hub</h4>
                            <p className="text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none">Save $400/week in parking</p>
                        </div>
                    </div>
                    <div className="flex gap-4 items-start">
                        <div className="p-3 bg-emerald-100 text-emerald-600 rounded-2xl"><Icon name="shopping-cart" /></div>
                        <div>
                            <h4 className="font-black text-slate-900">Grocery Run</h4>
                            <p className="text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none">City Market > Resort Dining</p>
                        </div>
                    </div>
                    <div className="flex gap-4 items-start">
                        <div className="p-3 bg-rose-100 text-rose-600 rounded-2xl"><Icon name="users" /></div>
                        <div>
                            <h4 className="font-black text-slate-900">Donation Culture</h4>
                            <p className="text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none">Free museums & parks</p>
                        </div>
                    </div>
                </div>
            </section>

            <section id="activities" className="py-20 max-w-7xl mx-auto px-6 text-center">
                <div className="mb-16">
                    <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-4">The <span className="text-blue-600">Zero Dollar</span> List</h2>
                    <p className="text-slate-500 font-bold">Curated experiences that don't require a credit card swipe.</p>

                    <div className="inline-flex bg-slate-200/50 p-1.5 rounded-2xl mt-8">
                        {['free', 'low-cost', 'all'].map((cat) => (
                            <button
                                key={cat}
                                onClick={() => setActiveTab(cat)}
                                className={`px-8 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                                    activeTab === cat ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'
                                }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
                    {filteredActivities.map((activity) => (
                        <div key={activity.id} className="group bg-white rounded-[2rem] overflow-hidden border border-slate-100 transition-all hover:shadow-2xl card-hover flex flex-col h-full">
                            <div className="h-60 relative">
                                <img src={activity.image} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" alt={activity.title} />
                                <div className="absolute top-6 left-6 flex gap-2">
                                    <span className="px-3 py-1 rounded-full bg-white/95 text-[10px] font-black uppercase tracking-widest">{activity.tag}</span>
                                </div>
                                <div className={`absolute bottom-6 right-6 p-3 rounded-2xl shadow-xl text-white ${activity.category === 'free' ? 'bg-emerald-500' : 'bg-blue-600'}`}>
                                    <Icon name={activity.category === 'free' ? "smile" : "dollar-sign"} />
                                </div>
                            </div>
                            <div className="p-8 flex flex-col flex-grow">
                                <h3 className="text-2xl font-black mb-3">{activity.title}</h3>
                                <p className="text-slate-500 text-sm leading-relaxed mb-6 flex-grow">{activity.description}</p>
                                <div className="space-y-2 mb-8">
                                    {activity.highlights.map((h, i) => (
                                        <div key={i} className="flex items-center gap-2 text-xs font-bold text-slate-600">
                                            <Icon name="check" className="w-3 h-3 text-emerald-500" /> {h}
                                        </div>
                                    ))}
                                </div>
                                <button className="w-full py-4 rounded-2xl bg-slate-50 font-black text-slate-900 border border-slate-100 hover:bg-slate-900 hover:text-white transition-all text-sm uppercase tracking-widest">
                                    How to get there
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section id="conservation" className="py-24 bg-slate-900 text-white overflow-hidden text-center md:text-left">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        <div>
                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest mb-8">
                                <Icon name="shield-check" className="w-4 h-4" /> Rangers Legacy Stewardship
                            </div>
                            <h2 className="text-4xl md:text-6xl font-black mb-8 tracking-tighter">Support Nature for <span className="text-blue-400">Free</span></h2>
                            <p className="text-slate-400 text-lg mb-10 leading-relaxed max-w-xl">
                                Stewardship doesn't cost a dime. As part of the **Rangers Legacy** community, we invite you to hike with purpose. Observe, stay on trails, and keep our wildlife corridors clean.
                            </p>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="p-6 rounded-3xl bg-white/5 border border-white/10 group hover:border-blue-400 transition-colors">
                                    <Icon name="eye" className="text-blue-400 mb-3" />
                                    <h4 className="font-bold mb-1">Citizen Science</h4>
                                    <p className="text-xs text-slate-500 leading-relaxed font-medium">Use free apps to log wildlife sightings and help our board monitor herds.</p>
                                </div>
                                <div className="p-6 rounded-3xl bg-white/5 border border-white/10 group hover:border-emerald-400 transition-colors">
                                    <Icon name="navigation" className="text-emerald-400 mb-3" />
                                    <h4 className="font-bold mb-1">Path Protection</h4>
                                    <p className="text-xs text-slate-500 leading-relaxed font-medium">Staying on trail prevents erosion that costs millions in annual repair.</p>
                                </div>
                            </div>
                        </div>
                        <div className="relative flex justify-center lg:justify-end">
                            <div className="w-full max-w-md aspect-[4/5] rounded-[3rem] overflow-hidden border border-white/10 relative shadow-2xl">
                                <img src="https://images.unsplash.com/photo-1544198365-f5d60b6d8190?auto=format&fit=crop&q=80&w=1000" className="w-full h-full object-cover" alt="Conservation" />
                                <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent" />
                                <div className="absolute bottom-10 inset-x-10">
                                    <div className="bg-white/10 backdrop-blur-xl p-6 rounded-3xl border border-white/10 text-left">
                                        <p className="font-black text-xs uppercase tracking-widest text-blue-400 mb-2">A Message from the Board</p>
                                        <p className="text-sm font-medium italic text-slate-200 leading-relaxed">"The best things in Vail are wild and free. Help us keep it that way through smart thinking."</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="bg-white border-t border-slate-100 py-16 text-center">
                <div className="max-w-7xl mx-auto px-6">
                    <Icon name="mountain" className="w-10 h-10 text-blue-600 mb-8 mx-auto" />
                    <h3 className="text-2xl font-black tracking-tighter mb-4 uppercase">Vail Experience Hub</h3>
                    <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-12">Built for Locals, Travelers, and the Wild.</p>
                    <div className="flex justify-center gap-10 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        <a href="#" className="hover:text-blue-600 transition-colors">Hacks</a>
                        <a href="#" className="hover:text-blue-600 transition-colors">Free Parks</a>
                        <a href="#" className="hover:text-blue-600 transition-colors">Contact</a>
                    </div>
                </div>
            </section>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
'use strict';

var _slicedToArray = (function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i['return']) _i['return'](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError('Invalid attempt to destructure non-iterable instance'); } }; })();

var _React = React;
var useState = _React.useState;
var useEffect = _React.useEffect;

var Icon = function Icon(_ref) {
    var name = _ref.name;
    var className = _ref.className;

    useEffect(function () {
        if (window.lucide) window.lucide.createIcons();
    }, [name]);
    return React.createElement('i', { 'data-lucide': name, className: className });
};

var App = function App() {
    var _useState = useState('free');

    var _useState2 = _slicedToArray(_useState, 2);

    var activeTab = _useState2[0];
    var setActiveTab = _useState2[1];

    var _useState3 = useState(false);

    var _useState32 = _slicedToArray(_useState3, 2);

    var scrolled = _useState32[0];
    var setScrolled = _useState32[1];

    useEffect(function () {
        var handleScroll = function handleScroll() {
            return setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return function () {
            return window.removeEventListener('scroll', handleScroll);
        };
    }, []);

    var activities = [{
        id: 1,
        title: "The Free Bus System",
        category: "free",
        tag: "Transit Hack",
        description: "Avoid $30+ parking fees. Vail's internal bus system is 100% free and runs between the Village and Lionshead every few minutes.",
        highlights: ["Saves $30/day in parking", "Heated waiting areas", "Goes to grocery stores"],
        icon: "bus",
        image: "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=800"
    }, {
        id: 2,
        title: "Booth Falls Hike",
        category: "free",
        tag: "Nature",
        description: "A stunning 4-mile round trip hike to a massive waterfall. Incredible views of the valley for exactly zero dollars.",
        highlights: ["Iconic photo spots", "Wildlife sightings", "Accessible via free bus"],
        icon: "mountain",
        image: "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=800"
    }, {
        id: 3,
        title: "Snowsports Museum",
        category: "free",
        tag: "Culture",
        description: "Located in the Village parking structure. Learn about the 10th Mountain Division. Entry is free (donations welcome).",
        highlights: ["Indoor activity", "Historic artifacts", "Great for dating"],
        icon: "award",
        image: "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&q=80&w=800"
    }, {
        id: 4,
        title: "Village Picnic Spots",
        category: "free",
        tag: "Dating",
        description: "Skip the $100 lunches. Grab local groceries and eat by Gore Creek. Best romantic views without the bill.",
        highlights: ["River-side seating", "Quiet park areas", "Local's favorite"],
        icon: "heart",
        image: "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?auto=format&fit=crop&q=80&w=800"
    }, {
        id: 5,
        title: "Nature Discovery Center",
        category: "free",
        tag: "Kids",
        description: "Located at Eagle's Nest. If you hike up Berry Picker trail, access to this education center is totally free.",
        highlights: ["Interactive wildlife exhibits", "Naturalist programs", "Conservation focus"],
        icon: "tree-pine",
        image: "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&q=80&w=800"
    }, {
        id: 6,
        title: "Local Brewery Happy Hour",
        category: "low-cost",
        tag: "Social",
        description: "Vail Brewing Co (VBC) offers more affordable pints and a community vibe compared to hotel bars.",
        highlights: ["$7-9 Pints", "Dog friendly", "Food truck access"],
        icon: "beer",
        image: "https://images.unsplash.com/photo-1538333581680-72990666072b?auto=format&fit=crop&q=80&w=800"
    }];

    var filteredActivities = activeTab === 'all' ? activities : activities.filter(function (a) {
        return a.category === activeTab;
    });

    return React.createElement(
        'div',
        { className: 'min-h-screen' },
        React.createElement(
            'nav',
            { className: 'fixed w-full z-50 transition-all duration-300 ' + (scrolled ? 'glass-nav shadow-md py-3' : 'bg-transparent py-6') },
            React.createElement(
                'div',
                { className: 'max-w-7xl mx-auto px-6 flex justify-between items-center' },
                React.createElement(
                    'div',
                    { className: 'flex items-center gap-2' },
                    React.createElement(Icon, { name: 'mountain', className: 'w-8 h-8 ' + (scrolled ? 'text-blue-600' : 'text-white') }),
                    React.createElement(
                        'span',
                        { className: 'text-xl font-black tracking-tighter ' + (scrolled ? 'text-slate-900' : 'text-white') },
                        'VAIL LOCAL'
                    )
                ),
                React.createElement(
                    'div',
                    { className: 'hidden md:flex gap-8 items-center font-bold text-sm' },
                    React.createElement(
                        'a',
                        { href: '#hacks', className: scrolled ? 'text-slate-600' : 'text-white' },
                        'Budget Hacks'
                    ),
                    React.createElement(
                        'a',
                        { href: '#activities', className: scrolled ? 'text-slate-600' : 'text-white' },
                        'Free Stuff'
                    ),
                    React.createElement(
                        'button',
                        { className: 'bg-blue-600 text-white px-5 py-2 rounded-full shadow-lg' },
                        'Plan Your Move'
                    )
                )
            )
        ),
        React.createElement(
            'section',
            { className: 'relative h-[80vh] flex items-center justify-center text-center overflow-hidden' },
            React.createElement(
                'div',
                { className: 'absolute inset-0 z-0' },
                React.createElement('img', { src: 'https://images.unsplash.com/photo-1486496146582-9ffcd0b2b2b7?auto=format&fit=crop&q=80&w=2000', className: 'w-full h-full object-cover brightness-[0.45]', alt: 'Vail View' }),
                React.createElement('div', { className: 'absolute inset-0 hero-gradient' })
            ),
            React.createElement(
                'div',
                { className: 'relative z-10 max-w-4xl px-6' },
                React.createElement(
                    'h1',
                    { className: 'text-5xl md:text-8xl font-black mb-4 text-white tracking-tight leading-none' },
                    'Vail for the ',
                    React.createElement(
                        'span',
                        { className: 'text-emerald-400' },
                        'Rest of Us'
                    )
                ),
                React.createElement(
                    'p',
                    { className: 'text-lg md:text-xl text-slate-200 max-w-2xl mx-auto mb-10 font-medium' },
                    'Skip the $20 hot cocoa. Discover how to hike, play, and explore Vail for free (or close to it).'
                ),
                React.createElement(
                    'div',
                    { className: 'flex flex-col sm:flex-row gap-4 justify-center' },
                    React.createElement(
                        'a',
                        { href: '#activities', className: 'bg-emerald-500 text-white px-8 py-4 rounded-2xl font-black hover:bg-emerald-600 transition-all flex items-center justify-center gap-2' },
                        React.createElement(Icon, { name: 'search', className: 'w-5 h-5' }),
                        ' Find Free Activities'
                    )
                )
            )
        ),
        React.createElement(
            'section',
            { id: 'hacks', className: 'relative z-20 -mt-20 max-w-6xl mx-auto px-6 mb-24' },
            React.createElement(
                'div',
                { className: 'bg-white rounded-3xl p-8 shadow-2xl border border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-8' },
                React.createElement(
                    'div',
                    { className: 'flex gap-4 items-start' },
                    React.createElement(
                        'div',
                        { className: 'p-3 bg-blue-100 text-blue-600 rounded-2xl' },
                        React.createElement(Icon, { name: 'bus' })
                    ),
                    React.createElement(
                        'div',
                        null,
                        React.createElement(
                            'h4',
                            { className: 'font-black text-slate-900' },
                            'Free Bus Hub'
                        ),
                        React.createElement(
                            'p',
                            { className: 'text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none' },
                            'Save $400/week in parking'
                        )
                    )
                ),
                React.createElement(
                    'div',
                    { className: 'flex gap-4 items-start' },
                    React.createElement(
                        'div',
                        { className: 'p-3 bg-emerald-100 text-emerald-600 rounded-2xl' },
                        React.createElement(Icon, { name: 'shopping-cart' })
                    ),
                    React.createElement(
                        'div',
                        null,
                        React.createElement(
                            'h4',
                            { className: 'font-black text-slate-900' },
                            'Grocery Run'
                        ),
                        React.createElement(
                            'p',
                            { className: 'text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none' },
                            'City Market > Resort Dining'
                        )
                    )
                ),
                React.createElement(
                    'div',
                    { className: 'flex gap-4 items-start' },
                    React.createElement(
                        'div',
                        { className: 'p-3 bg-rose-100 text-rose-600 rounded-2xl' },
                        React.createElement(Icon, { name: 'users' })
                    ),
                    React.createElement(
                        'div',
                        null,
                        React.createElement(
                            'h4',
                            { className: 'font-black text-slate-900' },
                            'Donation Culture'
                        ),
                        React.createElement(
                            'p',
                            { className: 'text-xs text-slate-500 mt-1 uppercase font-bold tracking-widest leading-none' },
                            'Free museums & parks'
                        )
                    )
                )
            )
        ),
        React.createElement(
            'section',
            { id: 'activities', className: 'py-20 max-w-7xl mx-auto px-6 text-center' },
            React.createElement(
                'div',
                { className: 'mb-16' },
                React.createElement(
                    'h2',
                    { className: 'text-4xl md:text-6xl font-black tracking-tighter mb-4' },
                    'The ',
                    React.createElement(
                        'span',
                        { className: 'text-blue-600' },
                        'Zero Dollar'
                    ),
                    ' List'
                ),
                React.createElement(
                    'p',
                    { className: 'text-slate-500 font-bold' },
                    'Curated experiences that don\'t require a credit card swipe.'
                ),
                React.createElement(
                    'div',
                    { className: 'inline-flex bg-slate-200/50 p-1.5 rounded-2xl mt-8' },
                    ['free', 'low-cost', 'all'].map(function (cat) {
                        return React.createElement(
                            'button',
                            {
                                key: cat,
                                onClick: function () {
                                    return setActiveTab(cat);
                                },
                                className: 'px-8 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ' + (activeTab === cat ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500')
                            },
                            cat
                        );
                    })
                )
            ),
            React.createElement(
                'div',
                { className: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left' },
                filteredActivities.map(function (activity) {
                    return React.createElement(
                        'div',
                        { key: activity.id, className: 'group bg-white rounded-[2rem] overflow-hidden border border-slate-100 transition-all hover:shadow-2xl card-hover flex flex-col h-full' },
                        React.createElement(
                            'div',
                            { className: 'h-60 relative' },
                            React.createElement('img', { src: activity.image, className: 'w-full h-full object-cover group-hover:scale-105 transition-transform duration-700', alt: activity.title }),
                            React.createElement(
                                'div',
                                { className: 'absolute top-6 left-6 flex gap-2' },
                                React.createElement(
                                    'span',
                                    { className: 'px-3 py-1 rounded-full bg-white/95 text-[10px] font-black uppercase tracking-widest' },
                                    activity.tag
                                )
                            ),
                            React.createElement(
                                'div',
                                { className: 'absolute bottom-6 right-6 p-3 rounded-2xl shadow-xl text-white ' + (activity.category === 'free' ? 'bg-emerald-500' : 'bg-blue-600') },
                                React.createElement(Icon, { name: activity.category === 'free' ? "smile" : "dollar-sign" })
                            )
                        ),
                        React.createElement(
                            'div',
                            { className: 'p-8 flex flex-col flex-grow' },
                            React.createElement(
                                'h3',
                                { className: 'text-2xl font-black mb-3' },
                                activity.title
                            ),
                            React.createElement(
                                'p',
                                { className: 'text-slate-500 text-sm leading-relaxed mb-6 flex-grow' },
                                activity.description
                            ),
                            React.createElement(
                                'div',
                                { className: 'space-y-2 mb-8' },
                                activity.highlights.map(function (h, i) {
                                    return React.createElement(
                                        'div',
                                        { key: i, className: 'flex items-center gap-2 text-xs font-bold text-slate-600' },
                                        React.createElement(Icon, { name: 'check', className: 'w-3 h-3 text-emerald-500' }),
                                        ' ',
                                        h
                                    );
                                })
                            ),
                            React.createElement(
                                'button',
                                { className: 'w-full py-4 rounded-2xl bg-slate-50 font-black text-slate-900 border border-slate-100 hover:bg-slate-900 hover:text-white transition-all text-sm uppercase tracking-widest' },
                                'How to get there'
                            )
                        )
                    );
                })
            )
        ),
        React.createElement(
            'section',
            { id: 'conservation', className: 'py-24 bg-slate-900 text-white overflow-hidden text-center md:text-left' },
            React.createElement(
                'div',
                { className: 'max-w-7xl mx-auto px-6' },
                React.createElement(
                    'div',
                    { className: 'grid grid-cols-1 lg:grid-cols-2 gap-16 items-center' },
                    React.createElement(
                        'div',
                        null,
                        React.createElement(
                            'div',
                            { className: 'inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-black uppercase tracking-widest mb-8' },
                            React.createElement(Icon, { name: 'shield-check', className: 'w-4 h-4' }),
                            ' Rangers Legacy Stewardship'
                        ),
                        React.createElement(
                            'h2',
                            { className: 'text-4xl md:text-6xl font-black mb-8 tracking-tighter' },
                            'Support Nature for ',
                            React.createElement(
                                'span',
                                { className: 'text-blue-400' },
                                'Free'
                            )
                        ),
                        React.createElement(
                            'p',
                            { className: 'text-slate-400 text-lg mb-10 leading-relaxed max-w-xl' },
                            'Stewardship doesn\'t cost a dime. As part of the **Rangers Legacy** community, we invite you to hike with purpose. Observe, stay on trails, and keep our wildlife corridors clean.'
                        ),
                        React.createElement(
                            'div',
                            { className: 'grid grid-cols-1 sm:grid-cols-2 gap-4' },
                            React.createElement(
                                'div',
                                { className: 'p-6 rounded-3xl bg-white/5 border border-white/10 group hover:border-blue-400 transition-colors' },
                                React.createElement(Icon, { name: 'eye', className: 'text-blue-400 mb-3' }),
                                React.createElement(
                                    'h4',
                                    { className: 'font-bold mb-1' },
                                    'Citizen Science'
                                ),
                                React.createElement(
                                    'p',
                                    { className: 'text-xs text-slate-500 leading-relaxed font-medium' },
                                    'Use free apps to log wildlife sightings and help our board monitor herds.'
                                )
                            ),
                            React.createElement(
                                'div',
                                { className: 'p-6 rounded-3xl bg-white/5 border border-white/10 group hover:border-emerald-400 transition-colors' },
                                React.createElement(Icon, { name: 'navigation', className: 'text-emerald-400 mb-3' }),
                                React.createElement(
                                    'h4',
                                    { className: 'font-bold mb-1' },
                                    'Path Protection'
                                ),
                                React.createElement(
                                    'p',
                                    { className: 'text-xs text-slate-500 leading-relaxed font-medium' },
                                    'Staying on trail prevents erosion that costs millions in annual repair.'
                                )
                            )
                        )
                    ),
                    React.createElement(
                        'div',
                        { className: 'relative flex justify-center lg:justify-end' },
                        React.createElement(
                            'div',
                            { className: 'w-full max-w-md aspect-[4/5] rounded-[3rem] overflow-hidden border border-white/10 relative shadow-2xl' },
                            React.createElement('img', { src: 'https://images.unsplash.com/photo-1544198365-f5d60b6d8190?auto=format&fit=crop&q=80&w=1000', className: 'w-full h-full object-cover', alt: 'Conservation' }),
                            React.createElement('div', { className: 'absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent' }),
                            React.createElement(
                                'div',
                                { className: 'absolute bottom-10 inset-x-10' },
                                React.createElement(
                                    'div',
                                    { className: 'bg-white/10 backdrop-blur-xl p-6 rounded-3xl border border-white/10 text-left' },
                                    React.createElement(
                                        'p',
                                        { className: 'font-black text-xs uppercase tracking-widest text-blue-400 mb-2' },
                                        'A Message from the Board'
                                    ),
                                    React.createElement(
                                        'p',
                                        { className: 'text-sm font-medium italic text-slate-200 leading-relaxed' },
                                        '"The best things in Vail are wild and free. Help us keep it that way through smart thinking."'
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
        React.createElement(
            'footer',
            { className: 'bg-white border-t border-slate-100 py-16 text-center' },
            React.createElement(
                'div',
                { className: 'max-w-7xl mx-auto px-6' },
                React.createElement(Icon, { name: 'mountain', className: 'w-10 h-10 text-blue-600 mb-8 mx-auto' }),
                React.createElement(
                    'h3',
                    { className: 'text-2xl font-black tracking-tighter mb-4 uppercase' },
                    'Vail Experience Hub'
                ),
                React.createElement(
                    'p',
                    { className: 'text-slate-400 text-xs font-bold uppercase tracking-widest mb-12' },
                    'Built for Locals, Travelers, and the Wild.'
                ),
                React.createElement(
                    'div',
                    { className: 'flex justify-center gap-10 text-[10px] font-black text-slate-400 uppercase tracking-widest' },
                    React.createElement(
                        'a',
                        { href: '#', className: 'hover:text-blue-600 transition-colors' },
                        'Hacks'
                    ),
                    React.createElement(
                        'a',
                        { href: '#', className: 'hover:text-blue-600 transition-colors' },
                        'Free Parks'
                    ),
                    React.createElement(
                        'a',
                        { href: '#', className: 'hover:text-blue-600 transition-colors' },
                        'Contact'
                    )
                )
            )
        )
    );
};

var root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App, null));

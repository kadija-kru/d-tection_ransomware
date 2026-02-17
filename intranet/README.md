# Training Catalog - Company Intranet

A beautiful, modern training catalog page designed for company intranet use. Built with a focus on user experience and featuring your company's brand colors.

## 🎨 Design Features

### Company Colors Used
- **Primary Blue** (#2A3375) - Main branding, headers, buttons
- **Accent Pink** (#D92051) - Advanced level badges, gradient accents
- **Accent Yellow** (#FBBA00) - Statistics, gradient accents
- **Accent Light Blue** (#36BDE7) - Interactive elements, icons
- **Accent Green** (#2DAD75) - Beginner badges, success states

### User Experience Highlights
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Smooth Animations**: Engaging card animations and transitions
- **Live Search**: Real-time filtering as you type
- **Level Filtering**: Quick filter buttons for Beginner, Intermediate, and Advanced courses
- **Visual Hierarchy**: Clear typography and spacing for easy scanning
- **Accessibility**: Semantic HTML and keyboard shortcuts support

## 📁 Files

- `training-catalog.html` - Main HTML page
- `styles.css` - Complete styling with company colors
- `script.js` - Interactive functionality and JSON loading
- `training-data.json` - Sample training data (easily customizable)

## 🚀 How to Use

1. **Open the page**: Simply open `training-catalog.html` in a web browser
2. **Search trainings**: Use the search bar to find specific trainings
3. **Filter by level**: Click filter buttons to show only certain difficulty levels
4. **Enroll**: Click "Enroll Now" on any training card

## 🎯 Features

### Interactive Elements
- **Search Bar**: Searches across title, description, category, instructor, and tags
- **Filter Buttons**: Quick access to filter by training level
- **Hover Effects**: Cards lift on hover for better interactivity
- **Toast Notifications**: Confirmation when enrolling in a training
- **Keyboard Shortcuts**: 
  - `Ctrl/Cmd + K` to focus search
  - `Escape` to clear search

### Training Card Information
Each training displays:
- Level badge (Beginner/Intermediate/Advanced)
- Category
- Title and description
- Duration and start date
- Available seats with visual indicator
- Instructor with avatar
- Tags for easy categorization
- Enroll button

## 🔧 Customization

### Adding New Trainings
Edit `training-data.json` to add or modify trainings. Each training should have:
```json
{
  "id": 1,
  "title": "Training Name",
  "description": "Training description",
  "duration": "3 hours",
  "level": "Beginner|Intermediate|Advanced",
  "category": "Category Name",
  "instructor": "Instructor Name",
  "availableSeats": 25,
  "startDate": "2026-03-15",
  "tags": ["tag1", "tag2"]
}
```

### Modifying Colors
All colors are defined as CSS variables in `styles.css`:
```css
:root {
    --primary-blue: #2A3375;
    --accent-pink: #D92051;
    --accent-yellow: #FBBA00;
    --accent-light-blue: #36BDE7;
    --accent-green: #2DAD75;
}
```

## 📱 Responsive Breakpoints

- **Desktop**: 1280px and above (3 columns)
- **Tablet**: 768px - 1279px (2 columns)
- **Mobile**: Below 768px (1 column, optimized layout)

## ✨ Animation Effects

- Floating logo animation
- Staggered card entrance animations
- Smooth hover transitions
- Loading spinner
- Toast notification slide-in

## 🌐 Browser Support

Works on all modern browsers:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Opera (latest)

## 📄 License

This training catalog design is created for internal company use.

## 🤝 Support

For questions or customization requests, please contact your IT department.

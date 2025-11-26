import React, { useEffect, useState } from 'react';
import { Link, useRouterState } from '@tanstack/react-router';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import SearchIcon from '@mui/icons-material/Search';
import DescriptionIcon from '@mui/icons-material/Description';
import StorageIcon from '@mui/icons-material/Storage';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import SchoolIcon from '@mui/icons-material/School';

// Icon mapping
const iconMap = {
    Search: SearchIcon,
    Description: DescriptionIcon,
    Storage: StorageIcon,
    MonitorHeart: MonitorHeartIcon,
    School: SchoolIcon,
};

function Navigation() {
    const routerState = useRouterState();
    const currentPath = routerState.location.pathname;
    const [navItems, setNavItems] = useState([]);
    const [appName, setAppName] = useState('Error Classifier ML');

    useEffect(() => {
        // Fetch navigation items from backend
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                if (data.navigation) {
                    setNavItems(data.navigation);
                }
                if (data.app_name) {
                    setAppName(data.app_name);
                }
            })
            .catch(err => {
                console.error('Failed to fetch config:', err);
                // Fallback to default items
                setNavItems([
                    { path: '/', label: 'Search', icon: 'Search' },
                    { path: '/docs', label: 'Manage Docs', icon: 'Description' },
                    { path: '/dataset', label: 'Manage Dataset', icon: 'Storage' },
                    { path: '/exam', label: 'Exam Mode', icon: 'School' },
                    { path: '/status', label: 'Status', icon: 'MonitorHeart' },
                ]);
            });
    }, []);

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    {appName}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                    {navItems.map((item) => {
                        const IconComponent = iconMap[item.icon] || SearchIcon;
                        return (
                            <Button
                                key={item.path}
                                color="inherit"
                                component={Link}
                                to={item.path}
                                startIcon={<IconComponent />}
                                sx={{
                                    borderBottom: currentPath === item.path ? '2px solid white' : 'none',
                                }}
                                title={item.description}
                            >
                                {item.label}
                            </Button>
                        );
                    })}
                </Box>
            </Toolbar>
        </AppBar>
    );
}

export default Navigation;

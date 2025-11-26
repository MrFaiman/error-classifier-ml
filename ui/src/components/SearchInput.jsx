import React from 'react';
import {
    Button,
    CircularProgress,
    Grid,
    TextField,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import { useForm } from '@tanstack/react-form';

function SearchInput({ onSubmit, isSearching }) {
    const form = useForm({
        defaultValues: {
            errorMessage: '',
        },
        onSubmit: async ({ value }) => {
            onSubmit(value.errorMessage);
        },
    });

    return (
        <form
            onSubmit={(e) => {
                e.preventDefault();
                e.stopPropagation();
                form.handleSubmit();
            }}
        >
            <Grid container spacing={3}>
                <Grid item xs={12}>
                    <form.Field
                        name="errorMessage"
                        validators={{
                            onChange: ({ value }) =>
                                !value || value.trim().length === 0
                                    ? 'Please enter an error message'
                                    : undefined,
                        }}
                    >
                        {(field) => (
                            <TextField
                                fullWidth
                                multiline
                                rows={4}
                                label="Error Message"
                                placeholder="Enter the error message or log snippet..."
                                value={field.state.value}
                                onChange={(e) => field.handleChange(e.target.value)}
                                onBlur={field.handleBlur}
                                error={field.state.meta.errors.length > 0}
                                helperText={field.state.meta.errors[0]}
                                variant="outlined"
                            />
                        )}
                    </form.Field>
                </Grid>

                <Grid item xs={12}>
                    <Button
                        fullWidth
                        type="submit"
                        variant="contained"
                        size="large"
                        startIcon={
                            isSearching ? (
                                <CircularProgress size={20} color="inherit" />
                            ) : (
                                <SearchIcon />
                            )
                        }
                        disabled={isSearching}
                    >
                        {isSearching ? 'Classifying...' : 'Classify Error'}
                    </Button>
                </Grid>
            </Grid>
        </form>
    );
}

export default SearchInput;

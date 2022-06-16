import pandas as pd
import numpy as np
#regenerate identical synthetic data
np.random.seed(1234)
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pylab as plt
import ruptures as rpt


# Model Monitoring Utils
def generate_vlm_display(dfin, pdf_file, 
                         percentiles = [25,50,75], 
                         percentile_lines=False, 
                         change_points = None,
                         change_point_percentile_lines=True):
    df = dfin.copy()
    pdf_pages = PdfPages(pdf_file)
    nx,ny = np.shape(df)
    for i in range(ny):
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        
        # Create a figure instance (ie. a new page)
        fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
        ax1 = fig.add_subplot(111)
        
        # Plot variable-level data
        y_percentiles = np.percentile(y, percentiles) 
        str_pc1 = ', '.join([str(int(pc))+'%' for pc in percentiles])+' percentiles'
        str_pc2 = ', '.join([str(np.round(pc,2)) for pc in y_percentiles])
        
        
           
        # add change points
        str_pc0 = '\n'
        if change_points is not None:
            cpnow = change_points[change_points['feature_name']==feature_name]
            ncp = len(cpnow)
            if ncp > 1:
                str_pc0 = str(int(ncp-1))+' change points detected\n'
            for i2 in range(ncp):
                datetime = cpnow['datetime'].iloc[i2]
                if ((ncp > 1) and (i2 < ncp-1)):
                    ax1.axvline(datetime,color='k',linewidth=2)
                if change_point_percentile_lines:
                    ypc = cpnow['value'].iloc[i2]
                    ax1.axhline(ypc[0],ls=':',color='k')
                    ax1.axhline(ypc[1],ls='--',color='k')
                    ax1.axhline(ypc[2],ls=':',color='k')
                    
        str_pc = str_pc0+ str_pc1+'\n'+str_pc2
        
        label = feature_name+': '+ str_pc            
        ax1.plot(x, y,label=label,zorder=0)
        ax1.set_ylabel('value')
        
        #show percentiles
        if percentile_lines:
            if change_points is not None:
                cpnow = change_points[change_points['feature_name']==feature_name]
                if len(cpnow) > 0:
                    continue
            ax1.axhline(y_percentiles[0],ls=':',color='k')
            ax1.axhline(y_percentiles[1],ls='--',color='k')
            ax1.axhline(y_percentiles[2],ls=':',color='k')
        
        
        # titles
        ax1.set_title(feature_name)
        ax1.legend()
        plt.grid()
    
        # Done with the page
        pdf_pages.savefig(fig)
        
    # save change point data to pdf
    if change_points is not None:
        df_cp = change_points.copy()
        df_cp1 = df_cp.set_index(['feature_name','datetime'])
        df_cp2 = df_cp.drop_duplicates(subset='feature_name',keep='last').set_index(['feature_name','datetime'])
        df_cp3 = df_cp1.drop(df_cp2.index).round(2).reset_index()
        df_cp3 = df_cp3.set_index(['feature_name','datetime']).apply(pd.Series.explode).reset_index()
        df_cp3 = df_cp3[df_cp3['percentile']==df_cp3['percentile'].unique()[1]]
        if len(df_cp3)>0:
            fig = plt.figure()
            fig.suptitle('VLM Change Point Summary')
            table = plt.table(cellText=df_cp3.values, colLabels=df_cp3.columns, loc='center',
                  colWidths=[0.1 for col in range(df_cp3.columns.size)])
            table.auto_set_font_size(True)
            #table.set_fontsize(24)
            #table.scale(2, 2)
            plt.axis('off')
            pdf_pages.savefig()
    

    pdf_pages.close()


def calculate_change_points(dfin, percentiles= [25,50,75], explode=True, trend_penalty = 10, rolling_sd_window = 10, rolling_sd_penalty=10):
    df = dfin.copy()
    nx,ny = np.shape(df)
    df_cp = pd.DataFrame({})
    for i in range(ny):
        feature_name = df.columns[i]
        x = df.index
        y = df[feature_name].values
        algo = rpt.Pelt(model="rbf").fit(y)
        result = algo.predict(pen=10)
        
        
        #apply rolling standard deviation filter
        if rolling_sd_window is not None:
            yrsd = pd.Series(y).rolling(rolling_sd_window).std().shift(-int(rolling_sd_window/2)).dropna()
            algo = rpt.Pelt(model="rbf").fit(y)
            ap = algo.predict(pen=10)
            result = result + ap
            result = list(set(result))
            result.sort()
        
        
        
        idxlo = 0
        for r in result:
            yn = y[idxlo:r]
            y_pc = np.percentile(yn,percentiles)
            idxlo = r
            dfn = pd.DataFrame({'feature_name':[feature_name],'datetime':[x[min(nx-1,r)]],'percentile':[percentiles],'value':[y_pc]})
            df_cp = pd.concat([df_cp, dfn])
            
    df_cp['datetime']=pd.to_datetime(df_cp['datetime']).dt.date
    if explode:
        df_cp = df_cp.set_index(['feature_name','datetime']).apply(pd.Series.explode).reset_index()
    return df_cp
    
    
    
if __name__ == '__main__':

    # Ingest model input features data pull (previous-1yr)
    #
    #
    #
    ## this is just a template so create some synthetic data here
    n_features = 7
    n_history = 365
    end_date = pd.Timestamp.today().date()
    start_date = end_date - pd.Timedelta(str(int(n_history-1))+'D')
    dates = pd.date_range(start_date, end_date, freq='1d')
    X = np.random.randn(n_history,n_features)
    ## inject artificial feature offsets
    offsets = 5*np.random.randn(n_features)
    X = X + offsets
    ## inject artifical trend
    idx_trend_feature = 4
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    trend = 0.1*(np.arange(n_history) - idx_trend_start) + X[idx_trend_start,idx_trend_feature]
    trend[:idx_trend_start]=0
    trend[idx_trend_end:]=trend[idx_trend_end]
    X[:, idx_trend_feature] += trend 
    
    
    ## simulate dead-period
    idx_trend_feature = 5
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    X[idx_trend_start:idx_trend_end, idx_trend_feature] = 0
    
    ## volatility change
    idx_trend_feature = 6
    idx_trend_start = int(n_history/2)
    idx_trend_end = int(3/4*n_history)
    xm = X[idx_trend_start:idx_trend_end, idx_trend_feature].mean()
    X[idx_trend_start:idx_trend_end, idx_trend_feature] = (X[idx_trend_start:idx_trend_end, idx_trend_feature] - xm)*10 + xm
    
    
    
    
    df = pd.DataFrame(X,columns = ['feature_'+str(i) for i in range(n_features)])
    df.index = dates
    
    
    
    
    
    ## Change-point detection
    df_cp = calculate_change_points(df, percentiles= [25,50,75],explode=False)
    
    
    ## Monitoring Output
    pdf_file = './img/variable_level_monitoring.pdf'
    generate_vlm_display(df, pdf_file, percentiles = [25,50,75], change_points=df_cp)
    
    
    
    
    
    
    
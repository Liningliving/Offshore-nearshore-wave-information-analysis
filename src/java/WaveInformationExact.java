import java.nio.file.*;
import java.util.*;
import java.io.*;
import infodynamics.measures.continuous.kraskov.*;

/** Application adapter for official JIDT with exact elapsed-hour loading. */
public class WaveInformationExact {
  static double calculate(String measure,int[] hours,double[][] x,double[][] y,double[][] z,int k,int window)throws Exception {
    if(measure.equals("mi_height")) {
      MutualInfoCalculatorMultiVariateKraskov1 c=new MutualInfoCalculatorMultiVariateKraskov1();
      c.setProperty("NORMALISE","false");c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","4");
      ElapsedHourLoader.load(c,hours,x,y,k,window);return c.computeAverageLocalOfObservations();
    }
    ConditionalMutualInfoCalculatorMultiVariateKraskov1 c=new ConditionalMutualInfoCalculatorMultiVariateKraskov1();
    c.setProperty("NORMALISE","false");c.setProperty("NOISE_LEVEL_TO_ADD","0");c.setProperty("NUM_THREADS","4");
    ElapsedHourLoader.load(c,hours,x,y,z,k,window);return c.computeAverageLocalOfObservations();
  }
  public static void main(String[] args)throws Exception {
    String input=args[0],output=args[1],measure=args[2];
    if(!Arrays.asList("mi_height","cmi_period","cmi_direction").contains(measure))throw new IllegalArgumentException("Unknown measure");
    int k=Integer.parseInt(args[3]),window=Integer.parseInt(args[4]),count=Integer.parseInt(args[5]),bins=Integer.parseInt(args[6]);
    long seed=Long.parseLong(args[7]);
    List<String> lines=Files.readAllLines(Path.of(input)),times=Files.readAllLines(Path.of(args[8]));int n=lines.size();
    if(times.size()!=n)throw new IllegalArgumentException("Elapsed-hour index count mismatch");
    int[] hours=new int[n];double[][] data=new double[n][5];
    for(int i=0;i<n;i++){hours[i]=Integer.parseInt(times.get(i).trim());String[] f=lines.get(i).split(",");for(int j=0;j<5;j++)data[i][j]=Double.parseDouble(f[j]);}
    boolean mi=measure.equals("mi_height"),direction=measure.equals("cmi_direction");
    double[][] x=new double[n][direction?2:1],y=new double[n][1],z=new double[n][1];
    for(int i=0;i<n;i++){x[i][0]=data[i][mi?0:direction?3:2];if(direction)x[i][1]=data[i][4];y[i][0]=data[i][1];z[i][0]=data[i][0];}
    ElapsedHourLoader.validate(hours,x,y,z);
    double observed=calculate(measure,hours,x,y,z,k,window);double[] nulls=new double[count];
    Integer[] ranked=new Integer[n];for(int i=0;i<n;i++)ranked[i]=i;
    Arrays.sort(ranked,Comparator.comparingDouble(i->data[i][0]));Random random=new Random(seed);
    for(int b=0;b<count;b++){
      int[] order=new int[n];for(int i=0;i<n;i++)order[i]=i;
      if(bins==0){for(int i=n-1;i>0;i--){int j=random.nextInt(i+1),t=order[i];order[i]=order[j];order[j]=t;}}
      else for(int group=0;group<bins;group++){
        int start=group*n/bins,stop=(group+1)*n/bins;
        for(int i=stop-1;i>start;i--){int j=start+random.nextInt(i-start+1),a=ranked[i],c=ranked[j],t=order[a];order[a]=order[c];order[c]=t;}
      }
      double[][] shuffled=new double[n][];for(int i=0;i<n;i++)shuffled[i]=x[order[i]];
      // Do not use base computeSignificance: it can rebuild compressed time IDs.
      // Each fresh unmodified JIDT calculator receives the original time map.
      nulls[b]=calculate(measure,hours,shuffled,y,z,k,window);
    }
    try(PrintWriter out=new PrintWriter(output)){
      out.println("kind,index,nats,bits");out.printf(Locale.ROOT,"observed,0,%.17g,%.17g%n",observed,observed/Math.log(2));
      for(int i=0;i<count;i++)out.printf(Locale.ROOT,"surrogate,%d,%.17g,%.17g%n",i,nulls[i],nulls[i]/Math.log(2));
    }
    String audit="{\"elapsed_hour_indices_verified\":true,\"set_id\":0,\"observations\":"+n+",\"k\":"+k+",\"window_hours\":"+window+",\"direction_dimensions\":"+(direction?2:1)+",\"surrogate_timing_reload_checks\":"+count+"}\n";
    Files.writeString(Path.of(output+".timing.json"),audit);
    System.out.printf(Locale.ROOT,"%s n=%d k=%d exact_window_hours=%d B=%d bits=%.6f%n",measure,n,k,window,count,observed/Math.log(2));
  }
}
